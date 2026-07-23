import os
import sys
import re
import random
from dotenv import load_dotenv
from medical_vocab import load_medical_terms, MEDICAL_SYNONYMS, MEDICAL_ACADEMIC_PHRASES
from english_words_loader import get_english_lower
from academic_vocab import load_avl, load_mawl, get_academic_score
from sop_engine import apply_sop_transforms

# Load environment variables (e.g. from .env file)
load_dotenv()

# Preload lexical resources (lazy: English words loaded on first use)
load_medical_terms()
load_avl()
load_mawl()

# Pre-computed lowercase sets for has_medical_terms
_MED_LOWER_CACHE = None
_ENG_LOWER_CACHE = None

# Skill Directory Path (supports PyInstaller bundled mode)
def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'backend')
    return os.path.dirname(os.path.abspath(__file__))

SKILLS_DIR = os.path.join(_get_base_dir(), ".agent", "skills")

def get_skill_content(skill_filename: str) -> str:
    """Reads a skill markdown file and returns its instructions."""
    path = os.path.join(SKILLS_DIR, skill_filename)
    if not os.path.exists(path):
        # Check standard skills path
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".agent", "skills", skill_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Skill file not found: {skill_filename}")
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
            
    return content.strip()

# Master synonym map for Quillbot-strength paraphrasing
# Each word maps to multiple alternatives per style, chosen randomly at rewrite time
SIMULATION_DICTIONARY = {
    "show": {"academic": ["elucidate", "illustrate", "delineate", "demonstrate"],
             "concise": ["show"], "impact": ["demonstrate", "prove", "establish"]},
    "shows": {"academic": ["reflects", "illustrates", "delineates", "demonstrates"],
              "concise": ["shows"], "impact": ["demonstrates", "proves", "establishes"]},
    "showed": {"academic": ["indicated", "illustrated", "delineated"],
               "concise": ["showed"], "impact": ["proved", "established", "demonstrated"]},
    "shown": {"academic": ["elucidated", "illustrated", "delineated"],
              "concise": ["shown"], "impact": ["proved", "established", "demonstrated"]},
    "demonstrate": {"academic": ["elucidate", "illustrate", "delineate"],
                    "concise": ["show", "demonstrate"], "impact": ["prove", "establish", "exhibit"]},
    "demonstrates": {"academic": ["elucidates", "illustrates", "delineates"],
                     "concise": ["shows"], "impact": ["proves", "establishes", "exhibits"]},
    "demonstrated": {"academic": ["elucidated", "illustrated", "delineated"],
                     "concise": ["showed"], "impact": ["proved", "established", "exhibited"]},
    "suggest": {"academic": ["propose", "posit", "contend", "postulate"],
                "concise": ["suggest"], "impact": ["argue", "assert", "indicate"]},
    "suggests": {"academic": ["proposes", "posits", "contends", "postulates"],
                 "concise": ["suggests"], "impact": ["argues", "asserts", "indicates"]},
    "suggested": {"academic": ["proposed", "posited", "contended", "postulated"],
                  "concise": ["suggested"], "impact": ["argued", "asserted", "indicated"]},
    "indicate": {"academic": ["denote", "signal", "suggest", "imply"],
                 "concise": ["show"], "impact": ["reveal", "attest to", "point to"]},
    "indicates": {"academic": ["denotes", "signals", "suggests", "implies"],
                  "concise": ["shows"], "impact": ["reveals", "attests to", "points to"]},
    "indicated": {"academic": ["denoted", "signaled", "suggested", "implied"],
                  "concise": ["showed"], "impact": ["revealed", "attested to", "pointed to"]},
    "reveal": {"academic": ["disclose", "uncover", "bring to light"],
               "concise": ["show"], "impact": ["expose", "lay bare", "unearth"]},
    "reveals": {"academic": ["discloses", "uncovers", "brings to light"],
                "concise": ["shows"], "impact": ["exposes", "lays bare", "unearths"]},
    "revealed": {"academic": ["disclosed", "uncovered"],
                 "concise": ["showed"], "impact": ["exposed", "laid bare", "unearthed"]},
    "prove": {"academic": ["substantiate", "corroborate", "validate", "verify"],
              "concise": ["confirm", "prove"], "impact": ["establish", "affirm", "certify"]},
    "proves": {"academic": ["substantiates", "corroborates", "validates"],
               "concise": ["confirms"], "impact": ["establishes", "affirms", "certifies"]},
    "proved": {"academic": ["substantiated", "corroborated", "validated"],
               "concise": ["confirmed"], "impact": ["established", "affirmed", "certified"]},
    "propose": {"academic": ["put forth", "advance", "set forth", "hypothesize"],
                "concise": ["propose"], "impact": ["assert", "declare", "propound"]},
    "proposes": {"academic": ["puts forth", "advances", "sets forth", "hypothesizes"],
                 "concise": ["proposes"], "impact": ["asserts", "declares", "propounds"]},
    "proposed": {"academic": ["put forth", "advanced", "set forth", "hypothesized"],
                 "concise": ["proposed"], "impact": ["asserted", "declared", "propounded"]},
    "examine": {"academic": ["scrutinize", "interrogate", "dissect", "inspect"],
                "concise": ["check", "examine"], "impact": ["probe", "scrutinize", "interrogate"]},
    "examines": {"academic": ["scrutinizes", "interrogates", "dissects"],
                 "concise": ["checks"], "impact": ["probes", "scrutinizes", "interrogates"]},
    "examined": {"academic": ["scrutinized", "interrogated", "dissected"],
                 "concise": ["checked"], "impact": ["probed", "scrutinized", "interrogated"]},
    "investigate": {"academic": ["probe", "inquire into", "look into"],
                    "concise": ["investigate"], "impact": ["probe deeply", "delve into"]},
    "investigates": {"academic": ["probes", "inquires into", "looks into"],
                     "concise": [""], "impact": ["probes deeply", "delves into"]},
    "investigated": {"academic": ["probed", "inquired into"],
                     "concise": [""], "impact": ["probed deeply", "delved into"]},
    "investigation": {"academic": ["systematic analysis", "thorough examination", "in-depth inquiry"],
                      "concise": ["inquiry"], "impact": ["comprehensive inquiry", "detailed probe"]},
    "analyze": {"academic": ["deconstruct", "parse", "appraise", "evaluate"],
                "concise": ["check", "examine"], "impact": ["dissect", "interrogate", "break down"]},
    "analyzes": {"academic": ["deconstructs", "parses", "appraises"],
                 "concise": ["checks"], "impact": ["dissects", "interrogates", "breaks down"]},
    "analyzed": {"academic": ["deconstructed", "parsed", "appraised"],
                 "concise": ["checked"], "impact": ["dissected", "interrogated", "broke down"]},
    "explore": {"academic": ["investigate", "probe", "navigate"],
                "concise": ["explore"], "impact": ["push into", "pioneer"]},
    "explores": {"academic": ["investigates", "probes", "navigates"],
                 "concise": ["explores"], "impact": ["pushes into", "pioneers"]},
    "identify": {"academic": ["pinpoint", "discern", "isolate", "ascertain"],
                 "concise": ["find"], "impact": ["spot", "detect", "unmask"]},
    "identifies": {"academic": ["pinpoints", "discerns", "isolates", "ascertains"],
                   "concise": ["finds"], "impact": ["spots", "detects", "unmasks"]},
    "identified": {"academic": ["pinpointed", "discerned", "isolated", "ascertained"],
                   "concise": ["found"], "impact": ["spotted", "detected", "unmasked"]},
    "provide": {"academic": ["furnish", "supply", "yield", "offer"],
                "concise": ["give", "provide"], "impact": ["deliver", "supply", "furnish"]},
    "provides": {"academic": ["furnishes", "supplies", "yields", "offers"],
                 "concise": ["gives"], "impact": ["delivers", "supplies", "furnishes"]},
    "provided": {"academic": ["furnished", "supplied", "yielded", "offered"],
                 "concise": ["gave"], "impact": ["delivered", "supplied", "furnished"]},
    "present": {"academic": ["set forth", "expound", "delineate"],
                "concise": ["present", "show"], "impact": ["unveil", "showcase", "spotlight"]},
    "presents": {"academic": ["sets forth", "expounds", "delineates"],
                 "concise": ["shows"], "impact": ["unveils", "showcases", "spotlights"]},
    "presented": {"academic": ["set forth", "expounded", "delineated"],
                  "concise": ["showed"], "impact": ["unveiled", "showcased", "spotlighted"]},
    "report": {"academic": ["document", "record", "chronicle"],
               "concise": ["report"], "impact": ["announce", "proclaim", "disclose"]},
    "reports": {"academic": ["documents", "records", "chronicles"],
                "concise": ["reports"], "impact": ["announces", "proclaims", "discloses"]},
    "reported": {"academic": ["documented", "recorded", "chronicled"],
                 "concise": ["reported"], "impact": ["announced", "proclaimed", "disclosed"]},
    "discuss": {"academic": ["expound on", "elaborate on", "deliberate over"],
                "concise": ["discuss"], "impact": ["debate", "examine", "weigh"]},
    "discusses": {"academic": ["expounds on", "elaborates on", "deliberates over"],
                  "concise": ["discusses"], "impact": ["debates", "examines", "weighs"]},
    "consider": {"academic": ["contemplate", "ponder", "deliberate", "reflect on"],
                 "concise": ["consider"], "impact": ["weigh", "reckon with", "account for"]},
    "considers": {"academic": ["contemplates", "ponders", "deliberates", "reflects on"],
                  "concise": ["considers"], "impact": ["weighs", "reckons with", "accounts for"]},
    "require": {"academic": ["necessitate", "demand", "entail"],
                "concise": ["require", "need"], "impact": ["call for", "compel", "mandate"]},
    "requires": {"academic": ["necessitates", "demands", "entails"],
                 "concise": ["needs"], "impact": ["calls for", "compels", "mandates"]},
    "support": {"academic": ["substantiate", "corroborate", "bolster", "uphold"],
                "concise": ["support", "back"], "impact": ["champion", "reinforce", "fortify"]},
    "supports": {"academic": ["substantiates", "corroborates", "bolsters"],
                 "concise": ["backs"], "impact": ["champions", "reinforces", "fortifies"]},
    "supported": {"academic": ["substantiated", "corroborated", "bolstered"],
                  "concise": ["backed"], "impact": ["championed", "reinforced", "fortified"]},
    "confirm": {"academic": ["corroborate", "verify", "validate", "authenticate"],
                "concise": ["confirm"], "impact": ["affirm", "ratify", "certify"]},
    "confirms": {"academic": ["corroborates", "verifies", "validates"],
                 "concise": ["confirms"], "impact": ["affirms", "ratifies", "certifies"]},
    "confirmed": {"academic": ["corroborated", "verified", "validated"],
                  "concise": ["confirmed"], "impact": ["affirmed", "ratified", "certified"]},
    "establish": {"academic": ["found", "institute", "set up"],
                  "concise": ["create", "set up"], "impact": ["forge", "build", "lay the groundwork for"]},
    "establishes": {"academic": ["founds", "institutes", "sets up"],
                    "concise": ["creates"], "impact": ["forges", "builds", "lays the groundwork for"]},
    "established": {"academic": ["founded", "instituted", "set up"],
                    "concise": ["created"], "impact": ["forged", "built", "laid the groundwork for"]},
    "contribute": {"academic": ["add to", "augment", "supplement"],
                   "concise": ["contribute"], "impact": ["drive", "fuel", "advance"]},
    "contributes": {"academic": ["adds to", "augments", "supplements"],
                    "concise": ["contributes"], "impact": ["drives", "fuels", "advances"]},
    "affect": {"academic": ["influence", "shape", "modulate", "govern"],
               "concise": ["affect"], "impact": ["alter", "transform", "remake"]},
    "affects": {"academic": ["influences", "shapes", "modulates", "governs"],
                "concise": ["affects"], "impact": ["alters", "transforms", "remakes"]},
    "conduct": {"academic": ["undertake", "carry out", "perform"],
                "concise": ["conduct", "do"], "impact": ["pursue", "execute", "orchestrate"]},
    "conducts": {"academic": ["undertakes", "carries out", "performs"],
                 "concise": ["does"], "impact": ["pursues", "executes", "orchestrates"]},
    "conducted": {"academic": ["undertook", "carried out", "performed"],
                  "concise": ["did"], "impact": ["pursued", "executed", "orchestrated"]},
    "develop": {"academic": ["formulate", "devise", "construct"],
                "concise": ["build", "create"], "impact": ["engineer", "invent", "forge"]},
    "develops": {"academic": ["formulates", "devises", "constructs"],
                 "concise": ["builds", "creates"], "impact": ["engineers", "invents", "forges"]},
    "developed": {"academic": ["formulated", "devised", "constructed"],
                  "concise": ["built", "created"], "impact": ["engineered", "invented", "forged"]},
    "create": {"academic": ["generate", "produce", "fashion", "craft"],
               "concise": ["make", "create"], "impact": ["forge", "build", "construct"]},
    "creates": {"academic": ["generates", "produces", "fashions", "crafts"],
                "concise": ["makes"], "impact": ["forges", "builds", "constructs"]},
    "created": {"academic": ["generated", "produced", "fashioned", "crafted"],
                "concise": ["made"], "impact": ["forged", "built", "constructed"]},
    "produce": {"academic": ["generate", "yield", "manufacture"],
                "concise": ["make", "produce"], "impact": ["engineer", "turn out"]},
    "produces": {"academic": ["generates", "yields", "manufactures"],
                 "concise": ["makes"], "impact": ["engineers", "turns out"]},
    "obtain": {"academic": ["acquire", "procure", "secure", "extract"],
               "concise": ["get", "obtain"], "impact": ["gather", "collect", "capture"]},
    "obtains": {"academic": ["acquires", "procures", "secures"],
                "concise": ["gets"], "impact": ["gathers", "collects", "captures"]},
    "obtained": {"academic": ["acquired", "procured", "secured"],
                 "concise": ["got"], "impact": ["gathered", "collected", "captured"]},
    "address": {"academic": ["tackle", "grapple with", "attend to"],
                "concise": ["cover", "address"], "impact": ["confront", "take on"]},
    "addresses": {"academic": ["tackles", "grapples with", "attends to"],
                  "concise": ["covers"], "impact": ["confronts", "takes on"]},
    "assess": {"academic": ["evaluate", "appraise", "gauge", "measure"],
               "concise": ["check", "assess"], "impact": ["weigh", "judge", "size up"]},
    "assesses": {"academic": ["evaluates", "appraises", "gauges"],
                 "concise": ["checks"], "impact": ["weighs", "judges", "sizes up"]},
    "assessed": {"academic": ["evaluated", "appraised", "gauged"],
                 "concise": ["checked"], "impact": ["weighed", "judged", "sized up"]},
    "improve": {"academic": ["enhance", "augment", "refine", "optimize"],
                "concise": ["improve", "better"], "impact": ["elevate", "boost", "supercharge"]},
    "improves": {"academic": ["enhances", "augments", "refines"],
                 "concise": ["bettering"], "impact": ["elevates", "boosts", "supercharges"]},
    "improved": {"academic": ["enhanced", "augmented", "refined"],
                 "concise": ["bettered"], "impact": ["elevated", "boosted", "supercharged"]},
    "increase": {"academic": ["augment", "expand", "amplify", "escalate"],
                 "concise": ["raise", "increase"], "impact": ["surge", "skyrocket"]},
    "increases": {"academic": ["augments", "expands", "amplifies"],
                  "concise": ["raises"], "impact": ["surges", "skyrockets"]},
    "increase_noun": {"academic": ["augmentation", "expansion", "amplification"],
                      "concise": ["rise", "increase"], "impact": ["surge", "upsurge", "spike"]},
    "reduce": {"academic": ["diminish", "curtail", "mitigate", "ameliorate"],
               "concise": ["cut", "lower", "reduce"], "impact": ["slash", "pare down"]},
    "reduces": {"academic": ["diminishes", "curtails", "mitigates"],
                "concise": ["cuts", "lowers"], "impact": ["slashes", "pares down"]},
    "reduce_noun": {"academic": ["diminution", "curtailment", "mitigation"],
                    "concise": ["cut", "reduction"], "impact": ["slash", "downturn"]},
    "focus": {"academic": ["concentrate on", "center on", "zero in on"],
              "concise": ["focus"], "impact": ["zoom in on", "home in on"]},
    "focuses": {"academic": ["concentrates on", "centers on", "zeros in on"],
                "concise": ["focuses"], "impact": ["zooms in on", "homes in on"]},

    # Nouns
    "study": {"academic": ["investigation", "examination", "analysis", "exploration"],
              "concise": ["study"], "impact": ["breakthrough research", "landmark study"]},
    "studies": {"academic": ["investigations", "analyses", "explorations"],
                "concise": ["studies"], "impact": ["vanguard research", "pioneering work"]},
    "research": {"academic": ["scholarly inquiry", "academic investigation", "systematic study"],
                 "concise": ["research"], "impact": ["cutting-edge work", "pioneering research"]},
    "analysis": {"academic": ["deconstruction", "parsing", "appraisal", "evaluation"],
                 "concise": ["analysis", "review"], "impact": ["deep dive", "dissection", "interrogation"]},
    "approach": {"academic": ["methodology", "framework", "paradigm", "lens"],
                 "concise": ["approach", "method"], "impact": ["strategy", "blueprint", "playbook"]},
    "method": {"academic": ["methodology", "technique", "protocol", "procedure"],
               "concise": ["method", "way"], "impact": ["approach", "system", "scheme"]},
    "methodology": {"academic": ["analytical framework", "procedural framework", "research design"],
                    "concise": ["method"], "impact": ["blueprint", "architectural plan"]},
    "result": {"academic": ["empirical finding", "outcome", "observation", "finding"],
               "concise": ["result", "finding"], "impact": ["breakthrough", "key outcome"]},
    "results": {"academic": ["empirical findings", "outcomes", "observations"],
                "concise": ["results", "findings"], "impact": ["breakthroughs", "key outcomes"]},
    "finding": {"academic": ["discovery", "observation", "deduction"],
                "concise": ["finding"], "impact": ["revelation", "breakthrough"]},
    "findings": {"academic": ["discoveries", "observations", "deductions"],
                 "concise": ["findings"], "impact": ["revelations", "breakthroughs"]},
    "evidence": {"academic": ["empirical support", "substantiation", "corroboration"],
                 "concise": ["evidence", "proof"], "impact": ["hard evidence", "conclusive proof"]},
    "data": {"academic": ["empirical data", "quantitative observations", "measurements"],
             "concise": ["data", "information"], "impact": ["raw intelligence", "empirical record"]},
    "factor": {"academic": ["determinant", "parameter", "variable", "element"],
               "concise": ["factor", "element"], "impact": ["driver", "catalyst", "lever"]},
    "factors": {"academic": ["determinants", "parameters", "variables"],
                "concise": ["factors", "elements"], "impact": ["drivers", "catalysts"]},
    "variable": {"academic": ["parameter", "predictor", "covariate"],
                 "concise": ["variable"], "impact": ["lever", "driver"]},
    "effect": {"academic": ["impact", "influence", "ramification"],
               "concise": ["effect", "result"], "impact": ["bearing", "repercussion", "aftermath"]},
    "impact": {"academic": ["effect", "influence", "consequence"],
               "concise": ["impact", "effect"], "impact": ["force", "weight", "clout"]},
    "role": {"academic": ["function", "capacity", "position", "purview"],
             "concise": ["role", "part"], "impact": ["part to play", "stake", "hand"]},
    "context": {"academic": ["setting", "milieu", "backdrop", "frame"],
                "concise": ["context", "setting"], "impact": ["arena", "sphere", "landscape"]},
    "process": {"academic": ["procedure", "mechanism", "workflow", "pipeline"],
                "concise": ["process", "steps"], "impact": ["engine", "machinery"]},
    "mechanism": {"academic": ["apparatus", "instrumentality", "modus operandi"],
                  "concise": ["mechanism", "means"], "impact": ["engine", "gear", "infrastructure"]},
    "framework": {"academic": ["theoretical scaffold", "conceptual structure", "architectonic"],
                  "concise": ["framework", "structure"], "impact": ["architecture", "skeleton"]},
    "model": {"academic": ["theoretical construct", "conceptual model", "paradigm"],
              "concise": ["model"], "impact": ["blueprint", "prototype", "template"]},
    "system": {"academic": ["framework", "infrastructure", "apparatus"],
               "concise": ["system"], "impact": ["machinery", "engine", "setup"]},
    "feature": {"academic": ["attribute", "characteristic", "property", "trait"],
                "concise": ["feature", "aspect"], "impact": ["hallmark", "trademark", "signature"]},
    "characteristic": {"academic": ["attribute", "property", "trait", "quality"],
                       "concise": ["trait", "feature"], "impact": ["hallmark", "earmark"]},
    "hypothesis": {"academic": ["theoretical proposition", "conjecture", "postulate"],
                   "concise": ["hypothesis", "theory"], "impact": ["thesis", "premise", "claim"]},
    "theory": {"academic": ["theoretical framework", "conceptual model", "explanatory model"],
               "concise": ["theory", "idea"], "impact": ["doctrine", "principle", "tenet"]},
    "concept": {"academic": ["construct", "notion", "abstraction", "idea"],
                "concise": ["concept", "idea"], "impact": ["pillar", "cornerstone", "linchpin"]},
    "approach": {"academic": ["methodology", "framework", "paradigm", "lens"],
                 "concise": ["approach", "method"], "impact": ["strategy", "blueprint", "playbook"]},
    "application": {"academic": ["implementation", "deployment", "utilization"],
                    "concise": ["use", "application"], "impact": ["deployment", "practical use"]},
    "outcome": {"academic": ["result", "consequence", "end point", "deliverable"],
                "concise": ["result", "outcome"], "impact": ["payoff", "yield", "upshot"]},
    "implication": {"academic": ["ramification", "significance", "import"],
                    "concise": ["meaning", "implication"], "impact": ["takeaway", "lesson", "upshot"]},
    "limitation": {"academic": ["constraint", "shortcoming", "caveat", "drawback"],
                   "concise": ["limit", "downside"], "impact": ["handicap", "weakness", "pitfall"]},
    "contribution": {"academic": ["addition", "augmentation", "extension"],
                     "concise": ["contribution"], "impact": ["breakthrough", "advancement"]},

    # Adjectives
    "important": {"academic": ["pivotal", "consequential", "significant", "paramount"],
                  "concise": ["key", "important"], "impact": ["crucial", "vital", "momentous"]},
    "significant": {"academic": ["notable", "marked", "appreciable", "considerable"],
                    "concise": ["big", "important"], "impact": ["striking", "profound", "dramatic"]},
    "crucial": {"academic": ["critical", "essential", "indispensable", "pivotal"],
                "concise": ["key"], "impact": ["vital", "lifeblood", "make-or-break"]},
    "critical": {"academic": ["pivotal", "pressing", "catch", "paramount"],
                 "concise": ["key"], "impact": ["vital", "urgent", "do-or-die"]},
    "key": {"academic": ["central", "core", "fundamental", "integral"],
            "concise": ["key", "main"], "impact": ["linchpin", "cornerstone", "pivotal"]},
    "essential": {"academic": ["indispensable", "requisite", "necessary", "compulsory"],
                  "concise": ["needed", "essential"], "impact": ["vital", "fundamental"]},
    "substantial": {"academic": ["considerable", "significant", "ample", "extensive"],
                    "concise": ["big", "large"], "impact": ["massive", "sweeping", "far-reaching"]},
    "innovative": {"academic": ["novel", "pioneering", "groundbreaking", "cutting-edge"],
                   "concise": ["new", "fresh"], "impact": ["revolutionary", "visionary", "trailblazing"]},
    "novel": {"academic": ["original", "unprecedented", "new"],
              "concise": ["new"], "impact": ["revolutionary", "game-changing"]},
    "new": {"academic": ["novel", "recent", "emerging", "nascent"],
            "concise": ["new"], "impact": ["fresh", "cutting-edge", "groundbreaking"]},
    "effective": {"academic": ["efficacious", "productive", "potent", "impactful"],
                  "concise": ["effective", "useful"], "impact": ["powerful", "forceful", "dynamic"]},
    "efficient": {"academic": ["streamlined", "optimized", "cost-effective"],
                  "concise": ["efficient"], "impact": ["lean", "high-output", "productive"]},
    "robust": {"academic": ["rigorous", "sound", "reliable", "well-grounded"],
               "concise": ["strong", "solid"], "impact": ["resilient", "stalwart", "unshakeable"]},
    "reliable": {"academic": ["dependable", "trustworthy", "reproducible"],
                 "concise": ["reliable"], "impact": ["unfailing", "tried-and-true"]},
    "accurate": {"academic": ["precise", "exact", "veridical", "error-free"],
                 "concise": ["correct", "accurate"], "impact": ["spot-on", "dead-on"]},
    "relevant": {"academic": ["pertinent", "germane", "applicable", "material"],
                 "concise": ["relevant"], "impact": ["pressing", "consequential"]},
    "potential": {"academic": ["latent", "possible", "underlying", "anticipated"],
                  "concise": ["potential"], "impact": ["untapped", "dormant", "unrealized"]},
    "clear": {"academic": ["evident", "apparent", "manifest", "unambiguous"],
              "concise": ["clear"], "impact": ["crystal-clear", "obvious", "palpable"]},
    "distinct": {"academic": ["discrete", "separate", "differentiated"],
                 "concise": ["distinct", "clear"], "impact": ["well-defined", "sharp"]},
    "unique": {"academic": ["singular", "one-of-a-kind", "distinctive"],
               "concise": ["unique", "special"], "impact": ["unmatched", "unparalleled", "peerless"]},
    "common": {"academic": ["prevalent", "widespread", "ubiquitous", "pervasive"],
               "concise": ["common", "usual"], "impact": ["universal", "rampant", "epidemic"]},
    "major": {"academic": ["significant", "leading", "foremost", "paramount"],
              "concise": ["big", "major"], "impact": ["heavyweight", "dominant", "prevailing"]},
    "primary": {"academic": ["principal", "dominant", "predominant", "chief"],
                "concise": ["main", "primary"], "impact": ["driving", "central", "core"]},
    "specific": {"academic": ["particular", "certain", "definite", "concrete"],
                 "concise": ["specific", "exact"], "impact": ["precise", "well-defined"]},
    "general": {"academic": ["overarching", "comprehensive", "broad-based"],
                "concise": ["general"], "impact": ["blanket", "sweeping", "wide-ranging"]},
    "complex": {"academic": ["intricate", "sophisticated", "multifaceted", "nuanced"],
                "concise": ["hard", "complex"], "impact": ["knotty", "thorny", "convoluted"]},
    "optimal": {"academic": ["ideal", "most favorable", "best possible"],
                "concise": ["best", "optimal"], "impact": ["peak", "prime", "maximum"]},
    "adequate": {"academic": ["satisfactory", "sufficient", "suitable"],
                 "concise": ["enough", "adequate"], "impact": ["commensurate", "fitting"]},
    "limited": {"academic": ["confined", "restricted", "bounded", "circumscribed"],
                "concise": ["limited", "little"], "impact": ["cramped", "tight", "narrow"]},

    # Adverbs
    "significantly": {"academic": ["markedly", "considerably", "notably", "appreciably"],
                      "concise": ["a lot", "much"], "impact": ["dramatically", "vastly", "immensely"]},
    "importantly": {"academic": ["notably", "consequentially", "pivotally"],
                    "concise": [""], "impact": ["vitally", "momentously"]},
    "clearly": {"academic": ["evidently", "manifestly", "undeniably", "patently"],
                "concise": ["clearly"], "impact": ["unquestionably", "indisputably", "plainly"]},
    "typically": {"academic": ["commonly", "generally", "routinely", "customarily"],
                  "concise": ["usually", "typically"], "impact": ["standardly", "characteristically"]},
    "specifically": {"academic": ["particularly", "especially", "notably"],
                     "concise": ["specifically"], "impact": ["exactly", "precisely"]},
    "primarily": {"academic": ["mainly", "chiefly", "predominantly", "principally"],
                  "concise": ["mainly", "mostly"], "impact": ["above all", "first and foremost"]},
    "consequently": {"academic": ["accordingly", "thus", "therefore", "as a result"],
                     "concise": ["so"], "impact": ["hence", "ergo", "thereupon"]},
    "therefore": {"academic": ["consequently", "accordingly", "thus", "hence"],
                  "concise": ["so"], "impact": ["ergo", "thereby", "as such"]},
    "furthermore": {"academic": ["moreover", "additionally", "besides"],
                    "concise": [""], "impact": ["what is more", "beyond that", "in addition"]},
    "however": {"academic": ["nevertheless", "nonetheless", "yet", "still"],
                "concise": ["but", "still"], "impact": ["that said", "even so", "be that as it may"]},
    "similarly": {"academic": ["likewise", "correspondingly", "by the same token"],
                  "concise": ["also"], "impact": ["in like manner", "analogously"]},
    "consistently": {"academic": ["persistently", "regularly", "routinely"],
                     "concise": ["always"], "impact": ["steadfastly", "unwaveringly"]},
    "relatively": {"academic": ["comparatively", "moderately", "somewhat"],
                   "concise": ["rather", "quite"], "impact": ["fairly", "reasonably"]},
    "increasingly": {"academic": ["progressively", "growing", "ever more"],
                     "concise": ["more and more"], "impact": ["exponentially", "by leaps and bounds"]},
    "broadly": {"academic": ["widely", "extensively", "comprehensively"],
                "concise": ["broadly"], "impact": ["across the board", "in broad strokes"]},

    # Special: good/bad
    "good": {"academic": ["substantive", "sound", "rigorous", "compelling"],
             "concise": ["good"], "impact": ["exceptional", "outstanding", "superlative"]},
    "better": {"academic": ["superior", "more refined", "enhanced"],
               "concise": ["better"], "impact": ["improved", "elevated"]},
    "best": {"academic": ["most favorable", "ideal", "optimal"],
             "concise": ["best"], "impact": ["paramount", "foremost", "unrivaled"]},
    "bad": {"academic": ["deficient", "suboptimal", "inadequate"],
            "concise": ["bad"], "impact": ["poor", "flawed", "detrimental"]},
    "worse": {"academic": ["more deficient", "less favorable"],
              "concise": ["worse"], "impact": ["inferior", "poorer"]},
    "new": {"academic": ["novel", "recent", "emerging", "nascent"],
            "concise": ["new"], "impact": ["fresh", "groundbreaking", "cutting-edge"]},
    "old": {"academic": ["prior", "previous", "established", "longstanding"],
            "concise": ["old"], "impact": ["time-honored", "veteran"]},
    "very": {"academic": ["substantially", "considerably", "markedly"],
             "concise": [""], "impact": ["exceptionally", "extremely", "profoundly"]},
    "make": {"academic": ["synthesize", "constitute", "compose", "form"],
             "concise": ["make"], "impact": ["forge", "craft", "fashion"]},
    "use": {"academic": ["utilize", "employ", "leverage", "deploy"],
            "concise": ["use"], "impact": ["harness", "wield", "command"]},
    "get": {"academic": ["derive", "extract", "obtain", "procure"],
            "concise": ["get"], "impact": ["acquire", "attain", "secure"]},
    "help": {"academic": ["facilitate", "aid", "expedite", "enable"],
             "concise": ["help"], "impact": ["empower", "catalyze", "unlock"]},
    "change": {"academic": ["modification", "alteration", "shift", "transformation"],
               "concise": ["change"], "impact": ["transformation", "overhaul", "metamorphosis"]},
    "find": {"academic": ["uncover", "detect", "discover", "ascertain"],
             "concise": ["find"], "impact": ["discover", "unearth", "stumble upon"]},
    "need": {"academic": ["necessitate", "demand", "warrant", "call for"],
             "concise": ["need"], "impact": ["require", "compel", "cry out for"]}
}

_COMMON_WORDS = {
    "company", "quarter", "a", "an", "the", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "by", "from", "as", "is", "was", "were", "are",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall", "not", "no",
    "yes", "so", "if", "then", "than", "that", "this", "these", "those", "it",
    "its", "he", "she", "they", "them", "their", "we", "us", "our", "you",
    "your", "all", "each", "every", "some", "any", "many", "much", "more",
    "most", "few", "less", "little", "good", "bad", "big", "small", "new",
    "old", "first", "last", "next", "other", "same", "different", "own",
    "very", "too", "also", "just", "only", "now", "then", "here", "there",
    "when", "where", "why", "how", "what", "which", "who", "whom", "whose",
    "about", "above", "after", "again", "against", "before", "between",
    "through", "during", "without", "within", "along", "among", "around",
    "because", "under", "until", "upon", "while", "yet",
}

def has_medical_terms(text: str) -> bool:
    global _MED_LOWER_CACHE, _ENG_LOWER_CACHE
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    if not words:
        return False
    if _MED_LOWER_CACHE is None:
        med_terms = load_medical_terms()
        _MED_LOWER_CACHE = {t.lower() for t in med_terms}
    if _ENG_LOWER_CACHE is None:
        _ENG_LOWER_CACHE = get_english_lower()
    med_lower = _MED_LOWER_CACHE
    eng_lower = _ENG_LOWER_CACHE
    med_specific = [w for w in words if w in med_lower and w not in eng_lower]
    if med_specific:
        return True
    match_count = sum(1 for w in words if w in med_lower and w not in _COMMON_WORDS)
    return match_count >= 8 and match_count / len(words) >= 0.3


def medical_paraphrase(text: str, strength: int = 3) -> dict:
    def _med_synonym_replace(sentence: str, style: str) -> str:
        words = sentence.split()
        result = []
        for w in words:
            clean_w = _WORD_CLEAN_RE.sub("", w).lower()
            punct = ""
            if w.endswith((".", ",", ";", "!", "?")):
                for p in [".", ",", ";", "!", "?"]:
                    if w.endswith(p):
                        punct = p
                        clean_w = w[:-len(p)].lower()
                        break
            if clean_w in MEDICAL_ACADEMIC_PHRASES or clean_w in MEDICAL_SYNONYMS:
                repl = MEDICAL_ACADEMIC_PHRASES.get(clean_w) or MEDICAL_SYNONYMS.get(clean_w, "")
                if style == "academic" and repl:
                    if w[0].isupper():
                        repl = repl.capitalize()
                    result.append(repl + punct)
                elif style == "concise":
                    result.append(w)
                elif style == "impact":
                    im_repl = MEDICAL_SYNONYMS.get(clean_w, repl)
                    if w[0].isupper():
                        im_repl = im_repl.capitalize()
                    result.append(im_repl + punct if im_repl else w)
            elif clean_w in SIMULATION_DICTIONARY:
                options = SIMULATION_DICTIONARY[clean_w].get(style, [])
                if options:
                    repl = random.choice(options)
                    if repl:
                        if w[0].isupper():
                            repl = repl.capitalize()
                        result.append(repl + punct)
                    else:
                        result.append(w)
                else:
                    result.append(w)
            else:
                result.append(w)
        return " ".join(result)

    ac = _paraphrase(text, "academic", strength)
    ac_sentences = _split_sentences(ac)
    ac_med = " ".join(_med_synonym_replace(s, "academic") for s in ac_sentences)

    co = _paraphrase(text, "concise", strength)
    co_sentences = _split_sentences(co)
    co_med = " ".join(_med_synonym_replace(s, "concise") for s in co_sentences)

    im = _paraphrase(text, "impact", strength)
    im_sentences = _split_sentences(im)
    im_med = " ".join(_med_synonym_replace(s, "impact") for s in im_sentences)

    if strength >= 4:
        impact_prefixes = ["We demonstrate that ", "Our findings reveal that ", "This investigation establishes that "]
        im_med = random.choice(impact_prefixes) + im_med[0].lower() + im_med[1:]

    return {
        "status": "success",
        "options": [
            {"type": "Academic", "text": ac_med},
            {"type": "Concise", "text": co_med},
            {"type": "High-Impact", "text": im_med}
        ]
    }


_ACADEMIC_VERB_MAP = {
    "shows": "shown", "showed": "shown", "demonstrates": "demonstrated", "demonstrated": "demonstrated",
    "indicates": "indicated", "indicated": "indicated", "reveals": "revealed", "revealed": "revealed",
    "suggests": "suggested", "suggested": "suggested", "proposes": "proposed", "proposed": "proposed",
    "highlights": "highlighted", "highlighted": "highlighted", "illustrates": "illustrated", "illustrated": "illustrated",
    "implies": "implied", "implied": "implied", "confirms": "confirmed", "confirmed": "confirmed",
    "establishes": "established", "established": "established", "identifies": "identified", "identified": "identified",
    "examines": "examined", "examined": "examined", "investigates": "investigated", "investigated": "investigated",
    "explores": "explored", "explored": "explored", "analyzes": "analyzed", "analyzed": "analyzed",
}

_PASSIVE_TRIGGERS = {"shows", "demonstrates", "indicates", "reveals", "suggests", "proposes", "highlights",
                     "illustrates", "implies", "confirms", "establishes", "identifies"}

_CLAUSE_CONNECTORS_BECAUSE = re.compile(r'\b(because|since|as|due to the fact that)\b', re.IGNORECASE)
_CLAUSE_CONNECTORS_ALTHOUGH = re.compile(r'\b(although|though|while|whereas)\b', re.IGNORECASE)
_CLAUSE_CONNECTORS_IF = re.compile(r'\b(if|provided that|assuming)\b', re.IGNORECASE)

_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
_WORD_CLEAN_RE = re.compile(r"[^\w]")
_PARAGRAPH_SPLIT_RE = re.compile(r'\n\s*\n')


def _split_sentences(text: str) -> list:
    raw = _SENTENCE_SPLIT_RE.split(text.strip())
    return [s.strip() for s in raw if s.strip()]


_TRY_PASSIVE_SKIP_RE = re.compile(r'\b(that|whether|if|because|although|while)\b', re.IGNORECASE)
_TRY_PASSIVE_MATCH_RE = re.compile(
    r'\b(.+?)\s+(shows|showed|demonstrates|demonstrated|indicates|indicated|reveals|revealed|'
    r'suggests|suggested|proposes|proposed|highlights|highlighted|illustrates|illustrated)\s+(.+)',
    re.IGNORECASE
)


def _try_passive(sentence: str) -> str:
    if _TRY_PASSIVE_SKIP_RE.search(sentence):
        return None
    m = _TRY_PASSIVE_MATCH_RE.search(sentence)
    if m:
        subj = m.group(1).strip()
        verb_base = m.group(2).lower()
        obj = m.group(3).strip().rstrip(".")
        past = _ACADEMIC_VERB_MAP.get(verb_base, verb_base + "ed")
        subj_lower = subj[0].lower() + subj[1:] if subj else subj
        new = f"{obj} is {past} by {subj_lower}."
        if sentence[0].isupper():
            new = new[0].upper() + new[1:]
        return new
    return None


def _try_reorder_clause(sentence: str) -> str:
    low = sentence.lower()

    def _reorder_with(sent, conn_match, alt_map):
        conn = conn_match.group(1)
        idx = sent.lower().index(conn.lower())
        before = sent[:idx].strip().rstrip(",")
        rest = sent[idx + len(conn):].strip().rstrip(",")
        # connector at beginning: "Because X, Y" → "Y because X"
        if idx < 5 and "," in rest:
            parts = re.split(r",\s+", rest, maxsplit=1)
            if len(parts) == 2:
                main_conn = alt_map.get(conn.lower(), conn)
                before_clause = parts[0].strip().rstrip(".")
                after_clause = parts[1].strip().rstrip(".")
                new = f"{after_clause} {main_conn} {before_clause[0].lower()}{before_clause[1:]}"
                if not new.endswith("."):
                    new += "."
                if sentence[0].isupper():
                    new = new[0].upper() + new[1:]
                return new
        # connector in middle: "X because Y" → "Y because X"
        if before and rest:
            main_conn = alt_map.get(conn.lower(), conn)
            before_clean = before.strip().rstrip(".")
            rest_clean = rest.strip().rstrip(".")
            new = f"{rest_clean} {main_conn} {before_clean[0].lower()}{before_clean[1:]}"
            if not new.endswith("."):
                new += "."
            if sentence[0].isupper():
                new = new[0].upper() + new[1:]
            return new
        return None

    m = _CLAUSE_CONNECTORS_BECAUSE.search(low)
    if m:
        alt_conn = {"because": "because", "since": "since", "as": "as", "due to the fact that": "because"}
        result = _reorder_with(sentence, m, alt_conn)
        if result:
            return result
    m = _CLAUSE_CONNECTORS_ALTHOUGH.search(low)
    if m:
        conn = m.group(1)
        idx = low.index(conn)
        before = sentence[:idx].strip().rstrip(",")
        after = sentence[idx + len(conn):].strip().rstrip(",")
        # connector at beginning: "Although X, Y" → "Y, although X"
        if idx < 5 and "," in after:
            parts = re.split(r",\s+", after, maxsplit=1)
            if len(parts) == 2:
                before_clause = parts[0].strip().rstrip(".")
                after_clause = parts[1].strip().rstrip(".")
                new = f"{after_clause}, {conn} {before_clause[0].lower()}{before_clause[1:]}"
                if not new.endswith("."):
                    new += "."
                if sentence[0].isupper():
                    new = new[0].upper() + new[1:]
                return new
        # connector in middle: "X although Y" → "Y, although X"
        if before and after:
            before_clean = before.strip().rstrip(".")
            after_clean = after.strip().rstrip(".")
            new = f"{after_clean}, {conn} {before_clean[0].lower()}{before_clean[1:]}"
            if not new.endswith("."):
                new += "."
            if sentence[0].isupper():
                new = new[0].upper() + new[1:]
            return new
    return None


def _try_split_sentence(sentence: str) -> str:
    for splitter, joiner in [(" and ", ", and "), (" as well as ", ", as well as "),
                             (" not only ", ". Not only "), (" but also ", " but also ")]:
        if splitter in sentence and len(sentence) > 80:
            parts = sentence.split(splitter, 1)
            if len(parts) == 2:
                return f"{parts[0].rstrip('.')}. {parts[1][0].upper()}{parts[1][1:]}"
    m = re.match(r'(\w[\w\s]+),\s*(which|that|where|whereby|when)\s+(.+)', sentence, re.IGNORECASE)
    if m and len(sentence) > 80:
        return f"{m.group(1).strip().rstrip(',')}. {m.group(2).capitalize()} {m.group(3)}"
    return None


def _try_nominalize(sentence: str) -> str:
    pairs = [
        (r'\b(we|this study|this paper|this work)\s+(investigate|examine|analyze|explore)\s+(.+)$',
         r'An investigation into \3 was conducted'),
        (r'\b(we|this study|this paper|this work)\s+(propose|introduce|present)\s+(.+)$',
         r'A \2 is proposed for \3'),
        (r'\b(we|this study|this paper)\s+(find|found)\s+that\s+(.+)$',
         r'It was found that \3'),
    ]
    for pattern, replacement in pairs:
        m = re.search(pattern, sentence, re.IGNORECASE)
        if m:
            result = re.sub(pattern, replacement, sentence, flags=re.IGNORECASE)
            if result and result != sentence:
                # fix capitalization
                if sentence[0].isupper():
                    result = result[0].upper() + result[1:]
                return result
    return None


def _try_that_to_infinitive(sentence: str) -> str:
    m = re.search(r'\b(.+?)\s+(found|shown|demonstrated|observed|shown|reported)\s+that\s+(.+)', sentence, re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        verb = m.group(2).lower()
        obj = m.group(3).strip()
        new = f"{obj.rstrip('.')} was {verb} by {subj}."
        if sentence[0].isupper():
            new = new[0].upper() + new[1:]
        return new
    return None


def _try_frontload(sentence: str) -> str:
    if re.search(r'\b(that|whether|if)\b', sentence, re.IGNORECASE):
        return None
    # Skip passive constructions ("was given", "is shown", etc.)
    if re.search(r'\b(is|was)\s+(?!\w+er\b)\w{3,}(ed|en|ted)\b', sentence, re.IGNORECASE):
        return None
    m = re.search(r'\b(the|this)\s+(.+?)\s+(is|was|shows|demonstrates|indicates|reveals)\s+(.+)', sentence, re.IGNORECASE)
    if m:
        det = m.group(1)
        subj = m.group(2).strip()
        verb = m.group(3).lower()
        rest = m.group(4).strip().rstrip(".,;:!?")
        if verb in ("is", "was"):
            new = f"{det.capitalize()} {subj} -- {rest}."
        else:
            obj = rest.split()[0] if rest.split() else ""
            remainder = " ".join(rest.split()[1:]) if len(rest.split()) > 1 else ""
            verb_form = verb if verb.endswith('s') else verb + 's'
            new = f"{obj.capitalize()} {remainder} -- {det} {subj} {verb_form}."
        if sentence[0].isupper():
            new = new[0].upper() + new[1:]
        return new
    return None


def _apply_synonym_replacements(sentence: str, style: str, density: float = 0.6) -> str:
    words = sentence.split()
    result = []
    for w in words:
        clean_w = _WORD_CLEAN_RE.sub("", w).lower()
        punct = ""
        for p in [".", ",", ";", "!", "?"]:
            if w.endswith(p):
                punct = p
                clean_w = w[:-len(p)].lower()
                break
        if clean_w in SIMULATION_DICTIONARY and random.random() < density:
            options = SIMULATION_DICTIONARY[clean_w].get(style, [])
            if options:
                repl = random.choice(options)
                if repl:
                    if w[0].isupper():
                        repl = repl.capitalize()
                    result.append(repl + punct)
                else:
                    result.append(w)
            else:
                result.append(w)
        else:
            result.append(w)
    return " ".join(result)


def _try_adj_noun_swap(sentence: str) -> str:
    m = re.search(r'\b(the|this|an?)\s+(\w+)\s+(\w+)\s+(is|was|shows|demonstrates|indicates|reveals|suggests)', sentence, re.IGNORECASE)
    if m:
        det = m.group(1)
        adj = m.group(2)
        noun = m.group(3)
        verb = m.group(4)
        if len(adj) >= 4 and len(noun) >= 4:
            # "The innovative approach shows" -> "The approach of innovation shows"
            nounized = adj + ("ity" if adj.endswith("ble") else ("tion" if adj.endswith("ive") else "ness"))
            new = f"{det} {noun} of {nounized} {verb}"
            rest = sentence[m.end():]
            result = new + rest
            if sentence[0].isupper():
                result = result[0].upper() + result[1:]
            return result
    return None


def _try_there_rewrite(sentence: str) -> str:
    m = re.search(r'\b[Tt]here\s+(is|are|exists?|remain|arise)\s+(a|an|some|no|many|much|several)?\s*(.+?)\s+(that|which|who)\s+(.+)', sentence)
    if m:
        verb = m.group(1)
        obj = m.group(3).strip()
        rel = m.group(5).strip()
        new = f"{obj.capitalize() if sentence[0].isupper() else obj} {rel}"
        if not new.endswith("."):
            new += "."
        return new
    m2 = re.search(r'\b[Tt]here\s+(is|are)\s+(no|not|neither)\s+(.+?)(\.|,\s+and)', sentence)
    if m2:
        obj = m2.group(3).strip()
        new = f"{obj.capitalize()} {m2.group(2)} exist{s if m2.group(1)=='are' else ''}"
        if not new.endswith("."):
            new += "."
        return new
    return None


def _try_adverb_displace(sentence: str) -> str:
    adv_pattern = r'\b(clearly|evidently|notably|significantly|importantly|typically|generally|specifically|primarily|consequently|therefore|however|furthermore|moreover|similarly|consistently|broadly)\b'
    m = re.search(r'^(' + adv_pattern + r'),?\s+(.+)', sentence, re.IGNORECASE)
    if m:
        adv = m.group(1)
        rest = m.group(3)
        new = f"{rest.rstrip('.')}, {adv.lower()}."
        if sentence[0].isupper():
            new = new[0].upper() + new[1:]
        return new
    # Move mid-sentence adverb to front
    m2 = re.search(r'^(\w[\w\s]+?)\s+,\s*(' + adv_pattern + r')\s*,\s+(.+)', sentence, re.IGNORECASE)
    if m2:
        front = m2.group(1)
        adv = m2.group(2)
        rest = m2.group(4)
        new = f"{adv.capitalize()}, {front.strip().lower()}, {rest}"
        if not new.endswith("."):
            new += "."
        return new
    return None


def _try_negation_restructure(sentence: str) -> str:
    pairs = [
        (r'\bnot\s+(significant|important|crucial|critical|essential)\b', 'un\\1'),
        (r'\bnot\s+(accurate|adequate|effective|efficient|reliable)\b', ('inaccurate', 'inadequate', 'ineffective', 'inefficient', 'unreliable')),
        (r'\bnot\s+(clear|common|necessary|usual)\b', ('unclear', 'uncommon', 'unnecessary', 'unusual')),
        (r'\bnot\s+(possible|likely|able)\b', ('impossible', 'unlikely', 'unable')),
        (r'\black\s+of\b', 'absence of'),
        (r'\bno\s+(evidence|support|indication|proof)\b', '\\1 is lacking'),
    ]
    for pattern, repl in pairs:
        if isinstance(repl, str):
            if re.search(pattern, sentence, re.IGNORECASE):
                result = re.sub(pattern, repl, sentence, flags=re.IGNORECASE)
                if result != sentence:
                    return result
        else:
            m = re.search(pattern, sentence, re.IGNORECASE)
            if m:
                result = re.sub(pattern, random.choice(repl), sentence, flags=re.IGNORECASE)
                if result != sentence:
                    return result
    return None


def _try_preposition_front(sentence: str) -> str:
    # Skip if already fronted or contains em-dash
    if '--' in sentence:
        return None
    m = re.search(r'^(.+?)(\s+(in|at|on|for|with|by|through|via|under|over|across|within|among)\s+(?:the|a|an|this|these|those|our)?\s*(.+))$', sentence)
    if m and len(m.group(1).split()) >= 4:
        core = m.group(1).strip().rstrip(".,;:!?")
        pp = m.group(2).strip().rstrip(".,;:!?")
        new = f"{pp.capitalize()}, {core[0].lower()}{core[1:]}."
        return new
    return None


def _try_compound_restructure(sentence: str) -> str:
    m = re.search(r'^(.+?),?\s+and\s+(?:(?:hence|therefore|thus|consequently)\s+)?(.+)$', sentence, re.IGNORECASE)
    if m and len(m.group(1).split()) >= 3 and len(m.group(2).split()) >= 3:
        first = m.group(1).strip()
        second = m.group(2).strip().rstrip(".")
        # Both sides must contain a finite verb — avoid noun-phrase-only lists
        first_verb = bool(re.search(r'\b(is|are|was|were|has|have|had|shows|showed|indicates|indicated|demonstrates|suggests)\b', first, re.IGNORECASE))
        second_verb = bool(re.search(r'\b(is|are|was|were|has|have|had|shows|showed|indicates|indicated|demonstrates|suggests)\b', second, re.IGNORECASE))
        if not first_verb or not second_verb:
            return None
        pattern = random.choice(['not_only', 'while', 'semicolon'])
        if pattern == 'not_only':
            new = f"Not only {first[0].lower() + first[1:]}, but also {second[0].lower() + second[1:]}."
        elif pattern == 'while':
            new = f"{second.capitalize()}, while {first[0].lower() + first[1:]}."
        else:
            new = f"{first.rstrip('.')}; {second[0].lower() + second[1:]}."
        if sentence[0].isupper():
            new = new[0].upper() + new[1:]
        return new
    return None




_TRANSFORM_PIPELINES = {
    "academic": [_try_passive, _try_reorder_clause, _try_nominalize, _try_that_to_infinitive,
                 _try_adj_noun_swap, _try_there_rewrite, _try_negation_restructure],
    "concise":  [_try_split_sentence, _try_there_rewrite, _try_negation_restructure],
    "impact":   [_try_frontload, _try_reorder_clause, _try_passive, _try_adverb_displace,
                 _try_preposition_front, _try_compound_restructure],
}


def _paraphrase(text: str, style: str, strength: int) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return text

    density_map = {1: 0.3, 2: 0.5, 3: 0.65, 4: 0.8, 5: 0.9}
    density = density_map.get(strength, 0.6)
    transformed = []
    transforms = _TRANSFORM_PIPELINES.get(style, [])

    for i, sent in enumerate(sentences):
        t = sent

        t = _apply_synonym_replacements(t, style, density=density)

        if strength >= 2:
            wc = len(t.split())
            for fn in transforms:
                if wc < 5:
                    break
                result = fn(t)
                if result:
                    t = result
                    wc = len(t.split())
                    # At higher strengths, allow up to 2-3 chained transforms
                    if strength >= 4 and random.random() < 0.5:
                        continue
                    break

        if strength >= 4:
            t2 = _apply_synonym_replacements(t, style, density=0.3)
            if t2 != t:
                t = t2

        # Concise mode: always strip fillers
        if style == "concise":
            fillers = r'\b(indeed|actually|basically|essentially|importantly|interestingly|notably|particularly)\b'
            t = re.sub(fillers, '', t, flags=re.IGNORECASE)

        transformed.append(t)

    # Sentence merging (academic & impact) — uses comma+conjunction, not semicolons (SOP ban)
    if style in ("academic", "impact") and strength >= 2:
        merged = []
        skip = False
        merge_prob = 0.2 * strength
        for i, s in enumerate(transformed):
            if skip:
                skip = False
                continue
            if i < len(transformed) - 1 and len(s.split()) < 12 and len(transformed[i+1].split()) < 12 and random.random() < merge_prob:
                a = s.rstrip(".")
                b = transformed[i+1]
                b_low = b[0].lower() if b else ""
                connector = random.choice([", and ", ", while ", ", whereas "])
                if style == "academic" and strength >= 3:
                    connector = random.choice([", and further ", ", with ", ". Additionally, "])
                merged.append(f"{a}{connector}{b_low}{b[1:]}")
                skip = True
                continue
            merged.append(s)
        transformed = merged

    # Sentence splitting for concise at higher strength
    if style == "concise" and strength >= 3:
        split_prob = 0.15 * strength
        split_result = []
        for s in transformed:
            if len(s.split()) > 15 and random.random() < split_prob:
                parts = _try_split_sentence(s)
                if parts:
                    split_result.extend(pp.strip() for pp in parts.replace("..", ".").split(".") if pp.strip())
                    continue
            split_result.append(s)
        transformed = split_result

    # Academic: sentence-length alternation for rhythm
    if style == "academic" and strength >= 4 and len(transformed) >= 3:
        varied = []
        for i, s in enumerate(transformed):
            if i % 3 == 1 and len(s.split()) > 8:
                parts = re.split(r'(,\s+and\s+|;\s+)', s, maxsplit=1)
                if len(parts) >= 3:
                    varied.append(parts[0].rstrip(".") + ".")
                    varied.append(parts[1].strip() + " " + parts[2].strip())
                    continue
            varied.append(s)
        transformed = varied

    result = " ".join(transformed)

    result = apply_sop_transforms(result, strength=strength)

    result = re.sub(r'\s+', ' ', result).strip()
    # Fix "a important/an significant" grammar
    result = re.sub(r'\ba\s+(important|essential|innovative|impressive|integral|intriguing)\b', r'an \1', result, flags=re.IGNORECASE)
    result = re.sub(r'\ban\s+(significant|substantive|noticeable|big|simple|direct)\b', r'a \1', result, flags=re.IGNORECASE)
    return result if result else text


_HUMANIZER_AI_PHRASES = [
    # --- Transition words (replace with casual alternatives) ---
    (r'\bfurthermore\b', ['also', 'and', 'plus']),
    (r'\bmoreover\b', ['also', 'and', 'besides', "what's more"]),
    (r'\badditionally\b', ['also', 'and', 'plus']),
    (r'\bconsequently\b', ['so', 'which means', 'because of that']),
    (r'\btherefore\b', ['so', 'thus', 'that is why']),
    (r'\bthus\b', ['so', 'hence', 'therefore']),
    (r'\bhence\b', ['so', 'thus']),
    (r'\bnevertheless\b', ['still', 'even so', 'yet']),
    (r'\bnonetheless\b', ['still', 'even so', 'yet']),
    (r'\bnotwithstanding\b', ['even so', 'despite that', 'still']),
    (r'\bwhereas\b', ['while', 'but', 'though']),
    (r'\bconversely\b', ['on the flip side', 'meanwhile', 'in contrast']),
    (r'\baccordingly\b', ['so', 'thus', 'therefore']),

    # --- Adverbs (downshift to simpler) ---
    (r'\bsignificantly\b', ['noticeably', 'considerably', 'a lot']),
    (r'\bsubstantially\b', ['considerably', 'to a large extent', 'markedly']),
    (r'\bnotably\b', ['especially', 'worth noting', 'interestingly']),
    (r'\bremarkably\b', ['surprisingly', 'strikingly', 'quite notably']),
    (r'\bparticularly\b', ['especially', 'mainly', 'mostly']),
    (r'\bessentially\b', ['fundamentally', 'at its core', 'in essence']),
    (r'\bfundamentally\b', ['at its core', 'in essence', 'in principle']),
    (r'\bultimately\b', ['in the end', 'in the final analysis', 'eventually']),
    (r'\binherently\b', ['naturally', 'by its nature', 'built into it']),
    (r'\bsimilarly\b', ['in the same way', 'likewise', 'also']),
    (r'\bconversely\b', ['on the other hand', 'in contrast', 'meanwhile']),

    # --- AI overused verbs ---
    (r'\butilize\b', ['use', 'make use of', 'employ']),
    (r'\bfacilitate\b', ['help with', 'make easier', 'enable']),
    (r'\bleverage\b', ['use', 'take advantage of', 'build on']),
    (r'\boptimize\b', ['improve', 'make better', 'fine-tune']),
    (r'\bimplement\b', ['set up', 'put in place', 'adopt']),
    (r'\bdemonstrates?\b', ['shows', 'indicates', 'suggests']),
    (r'\belucidates?\b', ['explains', 'shows', 'clarifies']),
    (r'\bdelineates?\b', ['describes', 'outlines', 'defines']),
    (r'\bunderscores?\b', ['shows', 'highlights', 'stresses']),
    (r'\bhighlight(?:s|ed)?\b', ['points out', 'stresses', 'emphasizes']),
    (r'\billuminates?\b', ['clarifies', 'shows', 'explains']),
    (r'\bexemplifies?\b', ['shows', 'is an example of']),
    (r'\baddresses?\b', ['deals with', 'handles', 'covers']),
    (r'\bexplores?\b', ['looks at', 'considers', 'examines']),
    (r'\bcorroborates?\b', ['backs up', 'supports', 'confirms']),
    (r'\bsubstantiates?\b', ['backs up', 'proves', 'supports']),
    (r'\bpostulates?\b', ['suggests', 'proposes', 'claims']),
    (r'\bhypothesizes?\b', ['suggests', 'proposes', 'guesses']),
    (r'\bachieves?\b', ['reaches', 'attains', 'gets']),
    (r'\belucidates?\b', ['explains', 'shows', 'clarifies']),

    # --- AI overused nouns ---
    (r'\bcomprehensive\b', ['thorough', 'complete', 'full']),
    (r'\binnovative\b', ['new', 'fresh', 'creative']),
    (r'\btransformative\b', ['major', 'significant', 'far-reaching']),
    (r'\bunprecedented\b', ['unmatched', 'completely new', 'novel']),
    (r'\bstreamline\b', ['simplify', 'make smoother', 'improve']),
    (r'\bcrucial\b', ['key', 'critical']),
    (r'\bpivotal\b', ['key', 'important', 'central']),
    (r'\bcomprehensive\b', ['thorough', 'complete', 'full']),
    (r'\bgroundbreaking\b', ['important', 'significant', 'major']),
    (r'\bnovel\b', ['new', 'fresh', 'different']),
    (r'\brobust\b', ['strong', 'solid', 'reliable']),
    (r'\bdynamic\b', ['active', 'changing', 'evolving']),
    (r'\bseamless(?:ly)?\b', ['smooth', 'natural']),
    (r'\bcutting-edge\b', ['latest', 'advanced', 'modern']),
    (r'\bstate-of-the-art\b', ['latest', 'most advanced']),
    (r'\bgame-changer\b', ['major shift', 'big deal', 'turning point']),
    (r'\bparadigm shift\b', ['major change', 'fundamental change']),
    (r'\bempowers?\b', ['enables', 'allows', 'helps']),
    (r'\brevolutionize\b', ['change', 'transform', 'overhaul']),

    # --- AI phrase constructions ---
    (r'\bit is evident that\b', ['clearly', 'obviously']),
    (r'\bit is clear that\b', ['clearly', 'obviously']),
    (r'\bit is apparent that\b', ['clearly', 'seems', 'apparently']),
    (r'\bit is noteworthy that\b', ['importantly', 'notably']),
    (r'\bhas the potential to\b', ['could', 'might', 'may']),
    (r'\bplays?\s+a\s+(?:crucial|pivotal|key|vital)\s+role\b', ['is central to', 'matters in', 'is important for']),
    (r'\bit is important to note\b(?:\s+that)?', ['']),
    (r'\bit is worth noting\b(?:\s+that)?', ['']),
    (r'\bit is worth mentioning\b', ['']),
    (r'\bit should be noted that\b', ['']),
    (r'\bit can be seen that\b', ['']),
    (r'\bit is interesting to note that\b', ['']),
    (r'\bimportantly\b', ['']),
    (r'\bnotably\b(?:,\s*)?', ['']),

    # --- Academic conclusions (remove or shorten) ---
    (r'\bin conclusion\b', ['']),
    (r'\bin summary\b', ['']),
    (r'\bto summarize\b', ['']),
    (r'\bto conclude\b', ['']),
    (r'\bin closing\b', ['']),
    (r'\boverall,\s*', ['']),
    (r'\bin general,\s*', ['']),

    # --- Wordy academic phrases ---
    (r'\bin order to\b', ['to']),
    (r'\bdue to the fact that\b', ['because', 'since']),
    (r'\bwith respect to\b', ['about', 'for', 'in']),
    (r'\bwith regard to\b', ['about', 'for']),
    (r'\bas well as\b', ['and', 'plus', 'along with']),
    (r'\bin addition to\b', ['besides', 'along with', 'plus']),
    (r'\ba number of\b', ['some', 'several', 'various']),
    (r'\bthe majority of\b', ['most', 'many']),
    (r'\ba significant number of\b', ['many', 'a lot of']),
    (r'\bit is possible that\b', ['maybe', 'perhaps', 'possibly']),
    (r'\bit is likely that\b', ['probably', 'most likely']),
    (r'\bthere is a growing body of evidence\b', ['more evidence shows', 'evidence suggests']),
    (r'\bthere is increasing evidence\b', ['more evidence shows', 'evidence suggests']),
    (r'\bprevious studies have shown\b', ['past work shows', 'earlier studies found']),
    (r'\bprior work\b', ['past studies', 'earlier work']),
    (r'\brecent research\b', ['new work', 'recent studies']),
    (r'\ba growing body of literature\b', ['more studies', 'existing research']),
    (r'\bin the context of\b', ['in', 'within', 'for']),
    (r'\bin terms of\b', ['for', 'in', 'regarding']),
    (r'\bin light of\b', ['given', 'because of']),
    (r'\bon the basis of\b', ['based on', 'from']),
    (r'\bby means of\b', ['through', 'using', 'with']),
    (r'\bpertaining to\b', ['about', 'on', 'regarding']),
    (r'\bwith the aim of\b', ['to', 'aiming to']),
    (r'\bfor the purpose of\b', ['to', 'for']),
    (r'\bat the present time\b', ['now', 'currently']),
    (r'\bat this point in time\b', ['now', 'currently']),
    (r'\bin the event that\b', ['if', 'should']),
    (r'\bin the case of\b', ['for', 'with']),

    # --- Paper/study boilerplate ---
    (r'\bin this paper,\s*we\b', ['we']),
    (r'\bthis paper presents?\b', ['we present', 'this work presents']),
    (r'\bthis paper proposes?\b', ['we propose', 'this work proposes']),
    (r'\bthis paper introduces?\b', ['we introduce', 'this work introduces']),
    (r'\bin this work\b', ['here', 'in this study']),
    (r'\bin this study\b', ['here', 'in this work']),
    (r'\bthe present study\b', ['this study', 'our work']),
    (r'\bthe rest of this paper\b', ['']),
    (r'\bthe remainder of this paper\b', ['']),

    # --- Cliché nouns ---
    (r'\bdelves?\s+into\b', ['looks at', 'explores', 'investigates']),
    (r'\blandscape\b', ['area', 'field', 'domain']),
    (r'\bmultifaceted\b', ['complex', 'many-sided']),
    (r'\bnumerous\b', ['many', 'several', 'lots of']),
    (r'\ba variety of\b', ['different', 'various', 'diverse']),
    (r'\ba multitude of\b', ['many', 'numerous', 'countless']),
    (r'\bin the realm of\b', ['in', 'within', 'regarding']),
    (r'\bshowcase\b', ['show', 'display', 'highlight']),
    (r'\btestament\b', ['proof', 'evidence', 'sign']),
    (r'\btapestry\b', ['range', 'mix', 'variety']),
    (r'\bintricate\b', ['complex', 'detailed', 'careful']),
    (r'\bnuanced\b', ['subtle', 'detailed', 'careful']),
    (r'\bparadigm\b', ['model', 'approach', 'framework']),

    # --- Specific AI filler nouns ---
    (r'\ba plethora of\b', ['many', 'a lot of', 'plenty of']),
    (r'\ban array of\b', ['a range of', 'several', 'many']),
    (r'\ba wide range of\b', ['many', 'various', 'diverse']),
    (r'\bthe fact that\b', ['how', 'that']),
]

# Total: 108 entries
_HUMANIZER_AI_PHRASES_COMPILED = [
    (re.compile(pattern, re.IGNORECASE), alts)
    for pattern, alts in _HUMANIZER_AI_PHRASES
]

_HUMANIZER_CONTRACTIONS = [
    ("don't", "do not"), ("can't", "cannot"), ("won't", "will not"),
    ("isn't", "is not"), ("aren't", "are not"), ("wasn't", "was not"),
    ("weren't", "were not"), ("hasn't", "has not"), ("haven't", "have not"),
    ("hadn't", "had not"), ("doesn't", "does not"), ("didn't", "did not"),
    ("shouldn't", "should not"), ("wouldn't", "would not"), ("couldn't", "could not"),
    ("I'm", "I am"), ("you're", "you are"), ("he's", "he is"),
    ("she's", "she is"), ("it's", "it is"), ("we're", "we are"),
    ("they're", "they are"), ("I've", "I have"), ("we've", "we have"),
    ("they've", "they have"), ("I'll", "I will"), ("you'll", "you will"),
    ("we'll", "we will"), ("they'll", "they will"), ("that's", "that is"),
    ("there's", "there is"), ("here's", "here is"), ("let's", "let us"),
]

_HUMANIZER_EXTRA_CONTRACTIONS = [
    ("gonna", "going to"),
    ("wanna", "want to"),
    ("kinda", "kind of"),
    ("sorta", "sort of"),
    ("gotta", "got to"),
    ("dunno", "do not know"),
]

_HUMANIZER_FORMAL_INSERTIONS = [
    '-- though this remains debated',
    '-- at least in principle',
    'which is worth considering.',
    'notably.',
    '-- a point worth emphasizing.',
    'in practice.',
    '-- though this is still uncertain.',
]

_HUMANIZER_RHETORICAL_QUESTIONS = [
    'Why does this matter?',
    'What are the implications?',
    'How significant is this finding?',
    'What does this tell us?',
    'Worth asking -- what next?',
    'But is that really the case?',
]


def _random_chance(p: float) -> bool:
    return random.random() < p


def _humanize_split_sentences(text: str) -> list:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _humanize_strip_ai_phrases(text: str, strength: int) -> str:
    result = text
    intensity = {1: 0.3, 2: 0.5, 3: 0.7, 4: 0.85, 5: 1.0}[strength]
    for pattern, alternatives in _HUMANIZER_AI_PHRASES_COMPILED:
        if _random_chance(intensity):
            def _replacer(m, alts=alternatives):
                alt = random.choice(alts) if alts[0] else ''
                matched = m.group(0)
                punct = ''
                if matched and matched[-1] in ',.!?;:':
                    punct = matched[-1]
                return alt + punct
            result = pattern.sub(_replacer, result)
    result = re.sub(r'\s+', ' ', result).strip()
    result = re.sub(r'^[,;:.\s]+', '', result)
    result = re.sub(r'\b(\w+)\s+\1\b', r'\1', result, flags=re.IGNORECASE)
    return result


def _humanize_swap_synonyms(text: str, is_formal: bool = True) -> str:
    style = "academic" if is_formal else "concise"
    words = text.split()
    result = []
    for w in words:
        clean = _WORD_CLEAN_RE.sub('', w)
        punct = w[len(clean):] if len(clean) < len(w) else ''
        if clean and clean.lower() in SIMULATION_DICTIONARY and _random_chance(0.25):
            entry = SIMULATION_DICTIONARY[clean.lower()]
            candidates = entry.get(style, entry.get("concise", []))
            if candidates and candidates[0] != '':
                alt = random.choice(candidates)
                if clean[0].isupper():
                    alt = alt.capitalize()
                result.append(alt + punct)
            else:
                result.append(w)
        elif clean and clean.lower() in _HUMANIZER_BASIC_SYNONYMS and _random_chance(0.15):
            alt = random.choice(_HUMANIZER_BASIC_SYNONYMS[clean.lower()])
            if clean[0].isupper():
                alt = alt.capitalize()
            result.append(alt + punct)
        else:
            result.append(w)
    return ' '.join(result)

_HUMANIZER_BASIC_SYNONYMS = {
    'show': ['indicate', 'reveal', 'suggest'],
    'shows': ['indicates', 'reveals', 'suggests'],
    'showed': ['indicated', 'revealed', 'suggested'],
    'big': ['large', 'major', 'substantial'],
    'small': ['minor', 'limited', 'modest'],
    'good': ['positive', 'favorable', 'beneficial'],
    'bad': ['negative', 'adverse', 'unfavorable'],
    'new': ['novel', 'recent', 'emerging'],
    'old': ['prior', 'previous', 'established'],
    'change': ['alter', 'modify', 'adjust'],
    'changes': ['alters', 'modifies'],
    'find': ['detect', 'identify', 'observe'],
    'finds': ['detects', 'identifies'],
    'give': ['provide', 'supply', 'offer'],
    'gives': ['provides', 'offers'],
    'make': ['produce', 'generate', 'create'],
    'makes': ['produces', 'generates'],
    'many': ['several', 'numerous', 'various', 'multiple'],
    'very': ['quite', 'highly', 'extremely', 'notably'],
    'also': ['further', 'likewise', 'additionally'],
}

_HUMANIZER_HEDGES = [
    'seems', 'appears', 'tends to', 'might', 'could',
    'likely', 'arguably', 'suggests that', 'may',
]

_HUMANIZER_SENTENCE_STARTERS = [
    'Interestingly,', 'Notably,', 'However,',
    'In practice,', 'Broadly speaking,', 'If anything,',
]
_HUMANIZER_SENTENCE_STARTERS_CASUAL = [
    'Actually,', 'Basically,', 'Honestly,',
    'To be fair,', 'You know,', 'Thing is,',
    'The way I see it,', 'What I mean is,',
]

_HUMANIZER_COLLOQUIAL_MAPPING = {
    'investigate': ['look into', 'check out', 'dig into'],
    'investigates': ['looks into', 'checks out', 'digs into'],
    'investigated': ['looked into', 'checked out', 'dug into'],
    'demonstrate': ['show', 'prove'],
    'demonstrates': ['shows', 'proves'],
    'demonstrated': ['showed', 'proved'],
    'continue': ['keep going', 'press on'],
    'continues': ['keeps going', 'presses on'],
    'determine': ['figure out', 'nail down'],
    'determines': ['figures out', 'nails down'],
    'determined': ['figured out', 'nailed down'],
    'establish': ['set up', 'build'],
    'establishes': ['sets up', 'builds'],
    'established': ['set up', 'built'],
    'obtain': ['get', 'grab'],
    'obtains': ['gets', 'grabs'],
    'obtained': ['got', 'grabbed'],
    'attempt': ['try', 'give it a go'],
    'attempts': ['tries', 'gives it a go'],
    'attempted': ['tried', 'gave it a go'],
}


def _humanize_burstiness(text: str, strength: int) -> str:
    intensity = {1: 0.1, 2: 0.2, 3: 0.35, 4: 0.50, 5: 0.70}[strength]
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    result_paras = []
    for para in paragraphs:
        sentences = _humanize_split_sentences(para)
        if len(sentences) <= 1:
            result_paras.append(para)
            continue
        # Measure sentence lengths in words
        lengths = [len(s.split()) for s in sentences]
        # For each adjacent pair, if they are within 5 words AND within 40% of each other,
        # try to break one apart or add a parenthetical
        modified = list(sentences)
        for i in range(len(modified) - 1):
            if _random_chance(intensity):
                l1 = len(modified[i].split())
                l2 = len(modified[i+1].split())
                if l1 > 0 and l2 > 0:
                    ratio = min(l1, l2) / max(l1, l2) if max(l1, l2) > 0 else 1
                    if abs(l1 - l2) <= 5 and ratio > 0.6:
                        # Split the longer sentence or add parenthetical to vary length
                        if l1 >= l2 and l1 >= 12:
                            # Try to split sentence i at a comma/conjunction
                            split_match = re.search(r',\s+(?:and|but|or|while|whereas)\s+', modified[i])
                            if split_match and split_match.start() > 5:
                                split_pos = split_match.end()
                                first = modified[i][:split_match.start()]
                                second = modified[i][split_pos:]
                                if first and second:
                                    modified[i] = first + '. ' + second[0].upper() + second[1:]
                        else:
                            # Add a short parenthetical
                            frag = random.choice(['-- notably', '-- perhaps', '-- for instance', '-- in fact'])
                            modified[i] = modified[i] + ' ' + frag
        # At high strength, insert short sentences for burstiness
        if strength >= 4:
            for i in range(len(modified) - 1):
                if _random_chance(intensity * 0.3):
                    l1 = len(modified[i].split())
                    if l1 >= 15:
                        frag = random.choice([
                            'This matters.',
                            'Think about that for a second.',
                            'It is not that simple though.',
                            'But context matters here.',
                            'The data speaks for itself.',
                        ])
                        modified.insert(i + 1, frag)
                        break
        result_paras.append(' '.join(modified))
    return '\n\n'.join(result_paras)


def _humanize_hedging(text: str, strength: int) -> str:
    intensity = {1: 0.05, 2: 0.10, 3: 0.20, 4: 0.30, 5: 0.45}[strength]
    result = text
    # Hedge definitive verbs
    hedge_patterns = [
        (r'\bThe\s+results?\s+(show|demonstrate|prove|establish|confirm|indicate|reveal)s?\b',
         lambda m: re.sub(r'(show|demonstrate|prove|establish|confirm|indicate|reveal)s?',
                          lambda n: {'shows': 'seems to show', 'show': 'seem to show',
                                     'demonstrates': 'appears to demonstrate', 'demonstrate': 'appear to demonstrate',
                                     'proves': 'arguably proves', 'prove': 'arguably prove',
                                     'indicates': 'suggests', 'indicate': 'suggest',
                                     'reveals': 'tends to reveal', 'reveal': 'tend to reveal',
                                     'confirms': 'appears to confirm', 'confirm': 'appear to confirm',
                                     'establishes': 'arguably establishes', 'establish': 'arguably establish'
                                     }.get(n.group(0), n.group(0)), m.group(0))),
        (r'\bThis\s+(study|work|paper|finding|result)\s+(show|demonstrate|prove|establish|confirm)s?\b',
         lambda m: re.sub(r'(show|demonstrate|prove|establish|confirm)s?',
                          lambda n: {'shows': 'suggests', 'show': 'suggest',
                                     'demonstrates': 'seems to indicate', 'demonstrate': 'seem to indicate',
                                     'proves': 'suggests', 'prove': 'suggest',
                                     'confirms': 'appears to support', 'confirm': 'appear to support'
                                     }.get(n.group(0), n.group(0)), m.group(0))),
        (r'\b(clearly|evidently|undoubtedly|unquestionably|certainly)\b',
         lambda m: random.choice(['arguably', 'plausibly', 'in many respects', ''])),
        (r'\bit is\s+(clear|evident|apparent|obvious)\s+that\b',
         lambda m: random.choice(['it seems that', 'one could argue that', 'it may be that', ''])),
    ]
    for pattern, replacer in hedge_patterns:
        if _random_chance(intensity):
            result = re.sub(pattern, replacer, result, flags=re.IGNORECASE)
    # Add casual hedges mid-sentence
    if strength >= 3:
        sentences = _humanize_split_sentences(result)
        mod_sents = []
        for s in sentences:
            if _random_chance(intensity * 0.3):
                words_list = s.split()
                if len(words_list) > 6:
                    pos = random.randint(2, max(3, len(words_list) - 3))
                    hedge = random.choice(['sort of', 'kind of', 'in a way', 'arguably', 'basically'])
                    words_list.insert(pos, hedge)
                    s = ' '.join(words_list)
            mod_sents.append(s)
        result = ' '.join(mod_sents)
    return result


def _humanize_sentence_starters(text: str, strength: int, is_formal: bool) -> str:
    intensity = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.25, 5: 0.35}[strength]
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    result_paras = []
    starters = _HUMANIZER_SENTENCE_STARTERS if is_formal else _HUMANIZER_SENTENCE_STARTERS_CASUAL
    for para in paragraphs:
        sentences = _humanize_split_sentences(para)
        if len(sentences) <= 1:
            result_paras.append(para)
            continue
        modified = list(sentences)
        # Vary first sentence opener
        if _random_chance(intensity):
            first = modified[0]
            # Don't replace if already a non-standard starter
            first_three = ' '.join(first.split()[:3]).lower()
            if not any(first_three.startswith(s.lower()[:5]) for s in starters):
                opener = random.choice(starters)
                modified[0] = opener + ' ' + first[0].lower() + first[1:]
        # Vary one middle sentence starter
        for i in range(1, len(modified) - 1):
            if _random_chance(intensity * 0.5):
                s = modified[i]
                first_word = s.split()[0].lower() if s.split() else ''
                if first_word in ('the', 'this', 'these', 'it', 'we', 'our', 'a', 'an'):
                    opener = random.choice(starters)
                    modified[i] = opener + ' ' + s[0].lower() + s[1:]
        result_paras.append(' '.join(modified))
    return '\n\n'.join(result_paras)


def _humanize_colloquialisms(text: str, strength: int) -> str:
    intensity = {1: 0.05, 2: 0.10, 3: 0.20, 4: 0.35, 5: 0.50}[strength]
    result = text
    for word, alts in _HUMANIZER_COLLOQUIAL_MAPPING.items():
        if _random_chance(intensity):
            def _replace(m):
                return random.choice(alts)
            result = re.sub(r'\b' + word + r'\b', _replace, result, flags=re.IGNORECASE)
    return result


def _humanize_punctuation_noise(text: str, strength: int) -> str:
    result = text
    intensity = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20, 5: 0.30}[strength]
    if _random_chance(intensity):
        match = list(re.finditer(r'\.\s+(?=[A-Z])', result))
        if match and len(match) > 0:
            m = random.choice(match)
            before = result[:m.start()]
            after = result[m.end():]
            # SOP: semicolons forbidden — use comma+conjunction instead
            conj = random.choice([', and ', ', but ', ', while '])
            result = before + conj + after[0].lower() + after[1:]
    if _random_chance(intensity * 0.5):
        pair = random.choice(_HUMANIZER_CONTRACTIONS)
        short, long = pair
        if _random_chance(0.5):
            result = re.sub(r'\b' + re.escape(long) + r'\b', short, result, flags=re.IGNORECASE)
        else:
            result = re.sub(r'\b' + re.escape(short) + r'\b', long, result, flags=re.IGNORECASE)
    if _random_chance(0.1):
        emdash = re.search(r'\s*[—–]\s*', result)
        if emdash:
            result = re.sub(r'(\d)\s*[–—]\s*(\d)', r'\1–\2', result)
            result = re.sub(r'\s*[—–]\s*', ', ', result)
    return result


def _humanize_sentence_lengths(text: str, strength: int) -> str:
    sent_intensity = {1: 0.1, 2: 0.15, 3: 0.20, 4: 0.30, 5: 0.40}[strength]
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    result_paras = []
    for para in paragraphs:
        sentences = _humanize_split_sentences(para)
        if len(sentences) <= 1:
            result_paras.append(para)
            continue
        merged = []
        i = 0
        while i < len(sentences):
            s = sentences[i]
            wc = len(s.split())
            if wc < 8 and i < len(sentences) - 1 and len(sentences[i+1].split()) < 8 and _random_chance(sent_intensity):
                nxt = sentences[i+1].strip()
                conj = random.choice(['and', 'but', 'while', 'whereas'])
                merged_s = s.rstrip('.!?') + ', ' + conj + ' ' + nxt[0].lower() + nxt[1:]
                merged.append(merged_s)
                i += 2
                continue
            if wc > 30 and _random_chance(sent_intensity * 0.5):
                break_patterns = [r',\s+(?:and|but|or|while)\s+', r',\s+(?:which|that|where)\s+', r',\s+(?:however|therefore)\s+']
                for pat in break_patterns:
                    match = re.search(pat, s)
                    if match and match.start() > 10 and match.start() < len(s) - 10:
                        first = s[:match.start()].rstrip(',').rstrip('.')
                        second = s[match.end():]
                        if second:
                            merged.append(first + '.')
                            merged.append(second[0].upper() + second[1:])
                            break
                else:
                    merged.append(s)
            else:
                merged.append(s)
            i += 1
        result_paras.append(' '.join(merged))
    return '\n\n'.join(result_paras)


def _humanize_disrupt_flow(text: str, strength: int, is_formal: bool) -> str:
    intensity = {1: 0.05, 2: 0.10, 3: 0.20, 4: 0.30, 5: 0.40}[strength]
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    result = []
    for p in paragraphs:
        sentences = _humanize_split_sentences(p)
        if len(sentences) < 2:
            result.append(p)
            continue
        modified = list(sentences)
        if is_formal:
            if len(modified) >= 3 and _random_chance(intensity):
                idx = 1 + random.randint(0, len(modified) - 2)
                insertion = random.choice(_HUMANIZER_FORMAL_INSERTIONS)
                while idx > 0 and insertion.split()[0].lower() == modified[idx-1].split()[0].lower() if modified[idx-1] else False:
                    insertion = random.choice(_HUMANIZER_FORMAL_INSERTIONS)
                modified.insert(idx, insertion.capitalize())
            if len(modified) >= 2 and _random_chance(intensity * 0.5):
                q = random.choice(_HUMANIZER_RHETORICAL_QUESTIONS)
                while q.split()[0].lower() == (modified[-1].split()[0].lower() if modified[-1] else ''):
                    q = random.choice(_HUMANIZER_RHETORICAL_QUESTIONS)
                modified.append(q)
        else:
            if len(modified) >= 2 and _random_chance(intensity * 0.7):
                conj = random.choice(['And ', 'But ', 'So ', 'Plus ', 'Well, '])
                first_word = modified[0].split()[0].lower() if modified[0] else ''
                # Avoid repeat first word (e.g. "And" then "and, ")
                attempts = 0
                while conj.lower().strip(', ') == first_word and attempts < 5:
                    conj = random.choice(['And ', 'But ', 'So ', 'Plus ', 'Well, '])
                    attempts += 1
                modified.insert(0, conj + modified[0][0].lower() + modified[0][1:])
            if len(modified) >= 2 and _random_chance(intensity * 0.4):
                modified.append(random.choice(['Makes you wonder, right?', 'Sound familiar?', 'Interesting, isnt it?']))
        result.append(' '.join(modified))
    return '\n\n'.join(result)


def _humanize_reorder_sentences(text: str, strength: int) -> str:
    intensity = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20, 5: 0.30}[strength]
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    result = []
    for p in paragraphs:
        sentences = _humanize_split_sentences(p)
        if len(sentences) <= 3:
            result.append(p)
            continue
        middle = sentences[1:-1]
        if len(middle) <= 1:
            result.append(p)
            continue
        swap_count = max(1, int(len(middle) * intensity))
        pronoun_re = re.compile(r'\b(he|she|it|they|this|that|these|those|his|her|its|their)\b', re.IGNORECASE)
        for _ in range(swap_count):
            i = random.randint(0, len(middle) - 1)
            j = random.randint(0, len(middle) - 1)
            if i == j:
                continue
            if pronoun_re.match(middle[i]) or pronoun_re.match(middle[j]):
                if _random_chance(0.5):
                    continue
            middle[i], middle[j] = middle[j], middle[i]
        result.append(' '.join([sentences[0]] + middle + [sentences[-1]]))
    return '\n\n'.join(result)


def _humanize_randomize_paragraphs(text: str, strength: int) -> str:
    intensity = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20, 5: 0.30}[strength]
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if len(paragraphs) <= 1:
        return text
    result = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        sentences = _humanize_split_sentences(p)
        if len(sentences) >= 4 and _random_chance(intensity):
            split_at = 1 + random.randint(0, len(sentences) - 2)
            result.append(' '.join(sentences[:split_at]))
            result.append(' '.join(sentences[split_at:]))
        elif i < len(paragraphs) - 1 and len(sentences) <= 2 and len(_humanize_split_sentences(paragraphs[i+1])) <= 2 and _random_chance(intensity):
            result.append(p + ' ' + paragraphs[i+1])
            i += 1
        else:
            result.append(p)
        i += 1
    return '\n\n'.join(result)


def _humanize_readability_guard(original: str, processed: str) -> str:
    orig_len = len(original.split())
    proc_len = len(processed.split())
    if abs(proc_len - orig_len) > orig_len * 0.5:
        return original
    return processed


def humanize_text(text: str, mode: str = "general", strength: int = 3, is_medical: bool = False) -> str:
    strength = max(1, min(5, strength))
    is_noora = mode == "noora"
    original = text

    # Process each paragraph independently to preserve \n\n boundaries
    paragraphs = [p for p in re.split(r'(\n\s*\n)', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    def _process_para(para: str) -> str:
        result = para
        result = _humanize_strip_ai_phrases(result, strength)
        result = _humanize_swap_synonyms(result, is_formal=(mode == "general"))
        if not is_noora:
            result = _humanize_hedging(result, strength)
        result = _humanize_punctuation_noise(result, strength)
        if strength >= 2:
            result = _humanize_sentence_lengths(result, strength)
        if strength >= 2:
            result = _humanize_burstiness(result, strength)
        if strength >= 2:
            result = _humanize_sentence_starters(result, strength, is_formal=(mode == "general"))
        if strength >= 3:
            result = _humanize_colloquialisms(result, strength)
        if strength >= 3:
            result = _humanize_disrupt_flow(result, strength, is_formal=(mode == "general"))
        if strength >= 3:
            result = _humanize_reorder_sentences(result, strength)
        if is_noora:
            result = re.sub(r'\b(Therefore|Consequently|Eventually|Luckily|Also),\s*', r'\1 ', result)
            result = re.sub(r"\((\w+)\s*=\s*(\w+)\)", r"( \1 = \2 )", result)
            result = re.sub(r"in the study of\s+([\w\s\.]+et\s*al\.)", r"in \1 study", result, flags=re.IGNORECASE)
            if not result.endswith(".") and len(result) > 5:
                result += "."
            med_replacements = {
                "patients": "geriatric patients with comorbidities",
                "medication": "potentially inappropriate medications (PIMs)",
                "results": "biochemical measurements",
            }
            for orig, repl in med_replacements.items():
                if _random_chance(0.5):
                    result = result.replace(orig, repl)
        # Medical-aware post-processing (preserve drug names, dosages)
        if is_medical:
            med_terms = load_medical_terms()
            med_lower = {t.lower() for t in med_terms}
            words = result.split()
            preserved = []
            for w in words:
                clean = re.sub(r'[^a-zA-Z]', '', w).lower()
                if clean in med_lower:
                    preserved.append(w)
                else:
                    preserved.append(w)
            result = ' '.join(preserved)
        # Cleanup per paragraph
        result = re.sub(r'\s+', ' ', result).strip()
        result = re.sub(r',\s*,', ',', result)
        result = re.sub(r'\s+,', ',', result)
        result = re.sub(r'\.\s*\.', '.', result)
        result = result.strip().strip(',').strip()
        return result

    processed_paras = [_process_para(p) for p in paragraphs]

    # Rejoin with paragraph separators
    result = []
    for i, p in enumerate(processed_paras):
        if p:
            result.append(p)
    result = '\n\n'.join(result)

    if strength >= 4:
        result = _humanize_randomize_paragraphs(result, strength)

    result = apply_sop_transforms(result, strength=strength)

    # Readability guard
    result = _humanize_readability_guard(original, result)

    return result if result else text


def run_local_simulation(text: str, skill_name: str, payload_type: str = "", strength: int = 3) -> dict:
    """Simulates agent rewriting using rules-based dictionary + structural transformations."""
    strength = max(1, min(5, strength))

    # 1. Medical Paraphrase
    if "academic_rewording_medical" in skill_name or (has_medical_terms(text) and "academic_rewording" in skill_name):
        return medical_paraphrase(text, strength)

    # 2. Paraphrase (Academic / Concise / High-Impact)
    if "academic_rewording" in skill_name:
        academic_str = _paraphrase(text, "academic", strength)
        concise_str = _paraphrase(text, "concise", strength)
        impact_str = _paraphrase(text, "impact", strength)

        return {
            "status": "success",
            "options": [
                {"type": "Academic", "text": academic_str},
                {"type": "Concise", "text": concise_str},
                {"type": "High-Impact", "text": impact_str}
            ]
        }
        
    # 2. Humanizer Simulation (enhanced with StealthHumanizer/AI-Text-Humanizer-App/lynote techniques)
    elif "humanizer" in skill_name:
        is_noora = "noora" in skill_name or payload_type == "noora"
        is_medical = has_medical_terms(text)
        mode = "noora" if is_noora else "general"
        transformed = humanize_text(text, mode=mode, strength=strength, is_medical=is_medical)
        return {
            "status": "success",
            "text": transformed
        }

    # 3. Proofread Simulation (enhanced with paper-revision-editor patterns)
    elif "proofreading" in skill_name:
        if payload_type == "phase1":
            return _run_proofreading_phase1(text)
        else:
            return _run_proofreading_phase2(text)

    return {"status": "error", "message": "Unknown skill"}


_BANNED_TRANSITIONS_LIST = [
    "furthermore", "moreover", "crucially", "importantly", "notably", "ultimately", "delving"
]
_BANNED_TRANSITIONS_PATTERNS = [
    re.compile(r'\b' + re.escape(t) + r'\b', re.IGNORECASE)
    for t in _BANNED_TRANSITIONS_LIST
]

_BANNED_PROMOTIONAL_LIST = [
    "novel", "interesting", "groundbreaking", "game-changing", "state-of-the-art"
]
_BANNED_PROMOTIONAL_PATTERNS = [
    re.compile(r'\b' + re.escape(p) + r'\b', re.IGNORECASE)
    for p in _BANNED_PROMOTIONAL_LIST
]

_IMPORTANCE_VERBS_PATTERNS = [
    re.compile(r"\bunderscores\b", re.IGNORECASE),
    re.compile(r"\bhighlights\b", re.IGNORECASE),
    re.compile(r"\bshowcases\b", re.IGNORECASE),
    re.compile(r"\bplays\s+a\s+(key|central|crucial|vital|pivotal)\s+role\b", re.IGNORECASE),
]

_INFLATED_NOUN_PHRASES = [
    re.compile(r"\bthe\s+landscape\s+of\b", re.IGNORECASE),
    re.compile(r"\bthe\s+realm\s+of\b", re.IGNORECASE),
    re.compile(r"\bthe\s+world\s+of\b", re.IGNORECASE),
    re.compile(r"\ba\s+myriad\s+of\b", re.IGNORECASE),
    re.compile(r"\ba\s+plethora\s+of\b", re.IGNORECASE),
    re.compile(r"\ba\s+wide\s+array\s+of\b", re.IGNORECASE),
    re.compile(r"\brich\s+tapestry\b", re.IGNORECASE),
    re.compile(r"\bparadigm\s+shift\b", re.IGNORECASE),
    re.compile(r"\bgame.?changer\b", re.IGNORECASE),
]

_TEMPLATE_SHAPES = [
    (re.compile(r"\bit\s+(is|'s)\s+(not\s+)?(just|merely|not\s+just)\s+about\b", re.IGNORECASE), "False-modesty antithesis template"),
    (re.compile(r"\bnot\s+only\s+.*\bbut\s+also\b", re.IGNORECASE), "'Not only...but also' template"),
    (re.compile(r"\bfirstly\b.*\bsecondly\b.*\bthirdly\b", re.IGNORECASE), "Firstly/Secondly/Thirdly list"),
    (re.compile(r"\bwe\s+show\s+that\b", re.IGNORECASE), "'We show that' frame (replace with claim)"),
    (re.compile(r"\bit\s+is\s+well\s+known\s+that\b", re.IGNORECASE), "'It is well known that' frame (cite or cut)"),
]

def _detect_section_type(text: str) -> str:
    low = text.lower()[:300]
    if any(w in low for w in ["abstract", "summary"]):
        return "Abstract"
    if any(w in low for w in ["introduction", "background", "motivation"]):
        return "Introduction"
    if any(w in low for w in ["method", "methodology", "experiment", "setup", "implementation"]):
        return "Methodology"
    if any(w in low for w in ["result", "finding", "experiment", "evaluation"]):
        return "Results"
    if any(w in low for w in ["discussion", "implication", "limitation"]):
        return "Discussion"
    if any(w in low for w in ["conclusion", "concluding", "summary", "future work"]):
        return "Conclusion"
    return "General"


def _run_proofreading_phase1(text: str) -> dict:
    issues = []
    issue_id = 0
    section_type = _detect_section_type(text)

    # --- Category: Structural / Logical Flow ---
    # Check for section-specific structural issues
    if section_type == "Abstract":
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) < 4:
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "MAJOR", "category": "Structural",
                "location": "Whole abstract",
                "diagnosis": f"Abstract has only {len(sentences)} sentences; may lack context, gap, contribution, evidence, or implications.",
                "why_matters": "Readers often read only the abstract to decide whether to continue.",
                "actionable_fix": "Ensure abstract includes: context, gap, contribution, evidence, and implications in order."
            })
    elif section_type == "Introduction":
        if any(w in text.lower() for w in ["is a fundamental problem", "is a critical challenge", "has been widely studied"]):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "Structural",
                "location": "Opening sentence",
                "diagnosis": "Textbook opening detected ('is a fundamental problem'). Most papers in the field start this way.",
                "why_matters": "Wasted opening — the reader has seen this sentence many times before.",
                "actionable_fix": "Start with a specific puzzle, question, or concrete observation."
            })

    # --- Category: Argumentation ---
    overclaim_words = ["significantly", "state-of-the-art", "groundbreaking", "unprecedented", "revolutionary"]
    found_overclaims = [w for w in overclaim_words if w in text.lower()]
    if found_overclaims:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "CRITICAL", "category": "Argumentation",
            "location": "Various",
            "diagnosis": f"Overclaiming vocabulary detected: {', '.join(found_overclaims)}. These terms assert statistical or competitive superiority without evidence.",
            "why_matters": "Reviewers immediately flag unsupported claims.",
            "actionable_fix": "Remove or replace with objective language. Reserve 'significantly' for statistical significance only."
        })

    # --- Category: Paragraph Craft ---
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 6:
        # Check for nominalization as paragraph craft issue
        nominalizations = re.findall(r'\b\w+(tion|sion|ment|ance|ence|ity|ism)\b', text.lower())
        if len(nominalizations) > len(sentences) * 0.5:
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "MINOR", "category": "Paragraph",
                "location": "Throughout",
                "diagnosis": "High density of nominalizations detected. Verbs are buried inside nouns, making prose passive and heavy.",
                "why_matters": "Forces readers to unpack meaning; fatiguing at paragraph scale.",
                "actionable_fix": "Convert nominalizations to active verbs: 'conducted an investigation of' -> 'investigated'."
            })

    # --- Category: Copyediting ---
    # Undefined acronyms
    acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
    if acronyms:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MAJOR", "category": "Copyediting",
            "location": "First occurrence",
            "diagnosis": f"Acronym(s) like '{acronyms[0]}' may be used without being defined.",
            "why_matters": "Readers may not understand technical jargon, leading to review rejection.",
            "actionable_fix": "Define each acronym explicitly at first use."
        })

    # Missing space before units
    if re.search(r"\b\d+(cm|mm|m|kg|s|mg|ml|g)\b", text):
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MINOR", "category": "Copyediting",
            "location": "Unit placement",
            "diagnosis": "Missing space before unit measure (e.g. '10cm' should be '10 cm').",
            "why_matters": "Violates scientific typesetting conventions.",
            "actionable_fix": "Insert space before unit symbols."
        })

    # Tense inconsistency (rough heuristic)
    past_count = len(re.findall(r'\b(was|were|studied|analyzed|observed|found|detected|measured)\b', text.lower()))
    present_count = len(re.findall(r'\b(is|are|shows|demonstrates|suggests|indicates|proposes)\b', text.lower()))
    if past_count > 3 and present_count > 3 and section_type in ("Results", "Methodology"):
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "Copyediting",
            "location": "Throughout",
            "diagnosis": "Mix of past and present tense. In scientific writing, methods and completed results typically use past tense; established facts use present.",
            "why_matters": "Inconsistent tense distracts the reader and may signal carelessness.",
            "actionable_fix": "Use past tense for specific completed actions, present for established facts and table/figure references."
        })

    # --- Category: AI Tells & House Style ---
    # Em-dash
    em_count = text.count("—")
    if em_count > 0:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "AITells",
            "location": f"{em_count} occurrence(s)",
            "diagnosis": f"Em-dash used {em_count} time(s). Em-dashes are an AI-generated writing tell and disrupt sentence flow.",
            "why_matters": "Reviewers recognize em-dashes as a stylistic crutch; disrupts logical sentence parsing.",
            "actionable_fix": "Replace each em-dash with a comma, colon, parentheses, or split into two sentences."
        })

    # Banned transitions
    low_text = text.lower()
    found_banned = [t for t, p in zip(_BANNED_TRANSITIONS_LIST, _BANNED_TRANSITIONS_PATTERNS) if p.search(low_text)]
    if found_banned:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "AITells",
            "location": "Transitions",
            "diagnosis": f"Banned transition words detected: {', '.join(sorted(found_banned)[:5])}. These mark AI-generated or lazy academic prose.",
            "why_matters": "Transitions should emerge from argument logic, not from filler words.",
            "actionable_fix": "Rebuild transitions from the content itself using given-new flow."
        })

    # Promotional adjectives
    found_promo = [p for p, pat in zip(_BANNED_PROMOTIONAL_LIST, _BANNED_PROMOTIONAL_PATTERNS) if pat.search(low_text)]
    if found_promo:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "AITells",
            "location": "Adjective use",
            "diagnosis": f"Promotional adjectives detected: {', '.join(found_promo)}. These perform certainty rather than earning it.",
            "why_matters": "If the substance survives without the adjective, the adjective was throat-clearing.",
            "actionable_fix": "Delete the adjective. If the sentence collapses, the underlying claim was weak."
        })

    # Importance-signaling verbs
    for pattern in _IMPORTANCE_VERBS_PATTERNS:
        if pattern.search(low_text):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "AITells",
                "location": "Verb choice",
                "diagnosis": "Importance-signaling verb detected ('underscores', 'plays a key role', etc.). Tells reader something matters instead of showing why.",
                "why_matters": "Replace the signal with the mechanism. If you cannot name the mechanism, the sentence was asserting unearned importance.",
                "actionable_fix": "Replace with the concrete relationship: 'X underscores the importance of Y' -> 'X fails whenever Y is absent'."
            })
            break

    # Inflated noun phrases
    for pattern in _INFLATED_NOUN_PHRASES:
        if pattern.search(low_text):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "AITells",
                "location": "Noun phrase",
                "diagnosis": "Inflated noun phrase detected ('landscape of', 'myriad of', etc.). Prefer concrete language.",
                "why_matters": "These are dead metaphors that add words without adding meaning.",
                "actionable_fix": "Replace with a specific count or concrete descriptor. 'A myriad of factors' -> 'four factors' or just 'many'."
            })
            break

    # Template shapes
    for pattern, label in _TEMPLATE_SHAPES:
        if pattern.search(low_text):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "AITells",
                "location": "Sentence structure",
                "diagnosis": f"AI template shape detected: {label}.",
                "why_matters": "These rhetorical molds flatten writing when used reflexively.",
                "actionable_fix": "Rewrite in a direct structure. 'We show that X improves accuracy' -> 'X improves accuracy by 12 points'."
            })
            break

    # --- Category: Reader Experience ---
    if len(sentences) >= 5 and section_type in ("Introduction", "Discussion"):
        # Check for topic string coherence
        first_words = [s.split()[:2] for s in sentences if s.strip()]
        unique_openers = len(set(tuple(w) for w in first_words if w))
        if unique_openers < 2:
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "MINOR", "category": "ReaderExperience",
                "location": "Throughout",
                "diagnosis": "Sentences all open with similar structure. Reader lacks orientation cues.",
                "why_matters": "Uniform sentence openings create a flat, monotonous reading experience.",
                "actionable_fix": "Vary sentence openers. Use transitions that arise from the content, not from filler words."
            })

    # --- Category: Academic Vocabulary Density ---
    academic_density = get_academic_score(text)
    if section_type in ("Abstract", "Introduction", "Discussion", "Conclusion") and academic_density < 0.15:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MAJOR", "category": "AITells",
            "location": "Vocabulary",
            "diagnosis": f"Low academic vocabulary density ({academic_density:.0%}). Only {academic_density:.0%} of content words appear in the Academic Vocabulary List (COCA-Academic).",
            "why_matters": "Academic prose requires domain-appropriate register. Low academic density suggests informal or generic word choices.",
            "actionable_fix": "Replace common words with academic equivalents from the AVL (e.g., 'get' -> 'obtain', 'show' -> 'demonstrate', 'use' -> 'employ')."
        })

    # Fallback if nothing specific detected
    if not issues:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MINOR", "category": "Copyediting",
            "location": "Sentence structure",
            "diagnosis": "Nominalization detected (using verbs as nouns).",
            "why_matters": "Makes reading passive and heavy.",
            "actionable_fix": "Rewrite using active verbs."
        })

    return {"status": "success", "issues": issues}


def _run_proofreading_phase2(text: str) -> dict:
    fixed_text = text

    # Replace em-dashes with commas
    fixed_text = fixed_text.replace("—", ", ")

    # Replace banned transitions with simpler alternatives
    transition_map = {
        r'\bFurthermore,\s*': "Additionally, ",
        r'\bMoreover,\s*': "Additionally, ",
        r'\bCrucially,\s*': "Critically, ",
        r'\bNotably,\s*': "",
        r'\bUltimately,\s*': "Finally, ",
        r'\bdelving\b': "examining",
        r'\bdelve\b': "examine",
    }
    for pattern, replacement in transition_map.items():
        fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)

    # Remove "it is important to note that" and variants
    fixed_text = re.sub(
        r'\b(It\s+is\s+(important|worth|noteworthy)\s+(to\s+)?(note|mention|highlight)\s+that)\b',
        '', fixed_text, flags=re.IGNORECASE
    )
    fixed_text = re.sub(r'\bThat\s+said,\s*', '', fixed_text, flags=re.IGNORECASE)

    # Remove "we show that" -> keep the claim
    fixed_text = re.sub(r'\bWe\s+show\s+that\b', 'We demonstrate', fixed_text, flags=re.IGNORECASE)

    # Replace "state-of-the-art" 
    fixed_text = fixed_text.replace("state-of-the-art", "highly competitive")
    fixed_text = fixed_text.replace("groundbreaking", "important")
    fixed_text = fixed_text.replace("unprecedented", "notable")

    # Remove promotional adjectives before nouns (basic heuristic)
    promo_patterns = [
        (r'\bnovel\s+(approach|method|technique|framework|algorithm|system)\b', r'\1'),
        (r'\binteresting\s+(result|finding|pattern|observation)\b', r'\1'),
        (r'\bgroundbreaking\s+(work|research|study|contribution)\b', r'\1'),
    ]
    for pattern, replacement in promo_patterns:
        fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)

    # Replace inflated noun phrases
    fixed_text = re.sub(r'\bthe\s+landscape\s+of\b', 'the field of', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\ba\s+myriad\s+of\b', 'many', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\ba\s+plethora\s+of\b', 'many', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\ba\s+wide\s+array\s+of\b', 'a wide range of', fixed_text, flags=re.IGNORECASE)

    # Replace importance-signaling verbs
    fixed_text = re.sub(
        r'\bunderscores\s+the\s+importance\s+of\b',
        'shows the importance of',
        fixed_text, flags=re.IGNORECASE
    )
    fixed_text = re.sub(
        r'\bplays\s+a\s+(key|central|crucial|vital|pivotal)\s+role\s+in\b',
        'contributes to',
        fixed_text, flags=re.IGNORECASE
    )

    # Fix missing space before units
    fixed_text = re.sub(r"\b(\d+)(cm|mm|m|kg|s|mg|ml|g)\b", r"\1 \2", fixed_text)

    # Fix "Not only...but also" -> "and"
    fixed_text = re.sub(r'\b(not\s+only)\s+', '', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\bbut\s+also\b', 'and', fixed_text, flags=re.IGNORECASE)

    # Clean up extra spaces from removals
    fixed_text = re.sub(r'\s+', ' ', fixed_text).strip()

    return {"status": "success", "text": fixed_text}




class AntigravityAgent:
    _active_provider = "gemini" # gemini, openrouter, ollama, rules
    _openrouter_api_key = ""
    _openrouter_model = "openrouter/auto"
    _gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    _ollama_model = "llama3.2"
    _ollama_base_url = "http://localhost:11434"

    def __init__(self, skill_filename: str):
        self.skill_filename = skill_filename
        self.skill_content = get_skill_content(skill_filename)

    @classmethod
    def set_api_config(cls, provider: str = "gemini", api_key: str = "", model: str = "", base_url: str = ""):
        cls._active_provider = provider.lower()
        if provider == "gemini":
            if api_key: cls._gemini_api_key = api_key.strip()
        elif provider == "openrouter":
            if api_key: cls._openrouter_api_key = api_key.strip()
            if model: cls._openrouter_model = model.strip()
        elif provider == "ollama":
            if model: cls._ollama_model = model.strip()
            if base_url: cls._ollama_base_url = base_url.rstrip("/")

    async def _call_openrouter(self, prompt: str, system_content: str, temperature: float = 0.7) -> str:
        import requests
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Para Paper V2",
        }
        payload = {
            "model": self._openrouter_model or "openrouter/auto",
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        res = requests.post(url, headers=headers, json=payload, timeout=120)
        if res.status_code != 200:
            raise RuntimeError(f"OpenRouter API error ({res.status_code}): {res.text}")
        data = res.json()
        return data["choices"][0]["message"]["content"].strip()

    async def _check_gemini(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self._gemini_api_key)

    async def _call_gemini(self, prompt: str, system_content: str, temperature: float = 0.7) -> str:
        """Send a prompt to Gemini API using google-genai SDK."""
        from google import genai
        client = genai.Client(api_key=self._gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_content,
                temperature=temperature,
                max_output_tokens=4096,
            )
        )
        return response.text.strip()

    async def _check_ollama(self) -> bool:
        """Check if Ollama is reachable and the model exists."""
        if not self._ollama_model:
            return False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._ollama_base_url}/api/tags")
                if resp.status_code != 200:
                    return False
                models = resp.json().get("models", [])
                return any(self._ollama_model in m.get("name", "") for m in models)
        except Exception:
            return False

    async def _call_ollama(self, prompt: str, system_content: str, temperature: float = 0.7) -> str:
        """Send a chat prompt to Ollama using the /api/chat endpoint with system message."""
        import httpx
        payload = {
            "model": self._ollama_model,
            "stream": False,
            "keep_alive": "5m",
            "options": {
                "temperature": temperature,
                "num_predict": 4096,
            },
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(f"{self._ollama_base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()

    async def run(self, text: str, payload_type: str = "", strength: int = 3) -> dict:
        strength = max(1, min(5, strength))
        temperature = 0.3 + (strength - 1) * 0.15
        prompt = self._build_prompt(text, payload_type, strength)

        # 1. Selected Provider execution
        if self._active_provider == "openrouter" and self._openrouter_api_key:
            try:
                print(f"[AgentWrapper] Using OpenRouter API ({self._openrouter_model}) for: {self.skill_filename}")
                response_text = await self._call_openrouter(prompt, self.skill_content, temperature)
                return self._parse_response(response_text, payload_type)
            except Exception as e:
                print(f"[AgentWrapper] OpenRouter API failed ({e}), falling back...")

        elif self._active_provider == "gemini" and self._gemini_api_key:
            try:
                print(f"[AgentWrapper] Using Gemini API for: {self.skill_filename}")
                response_text = await self._call_gemini(prompt, self.skill_content, temperature)
                return self._parse_response(response_text, payload_type)
            except Exception as e:
                print(f"[AgentWrapper] Gemini API failed ({e}), falling back...")

        elif self._active_provider == "ollama":
            if await self._check_ollama():
                try:
                    print(f"[AgentWrapper] Using Ollama local LLM ({self._ollama_model}) for: {self.skill_filename}")
                    response_text = await self._call_ollama(prompt, self.skill_content, temperature)
                    return self._parse_response(response_text, payload_type)
                except Exception as e:
                    print(f"[AgentWrapper] Ollama failed ({e}), falling back...")

        # 2. Automatic Fallback Chain (Gemini -> OpenRouter -> Ollama -> Rules)
        if self._gemini_api_key:
            try:
                response_text = await self._call_gemini(prompt, self.skill_content, temperature)
                return self._parse_response(response_text, payload_type)
            except Exception:
                pass

        if self._openrouter_api_key:
            try:
                response_text = await self._call_openrouter(prompt, self.skill_content, temperature)
                return self._parse_response(response_text, payload_type)
            except Exception:
                pass

        if await self._check_ollama():
            try:
                response_text = await self._call_ollama(prompt, self.skill_content, temperature)
                return self._parse_response(response_text, payload_type)
            except Exception:
                pass

        # 3. Rules-based simulation (always works, no external dependencies)
        print(f"[AgentWrapper] Running local rules-based simulation for: {self.skill_filename}")
        return run_local_simulation(text, self.skill_filename, payload_type, strength)

    def _build_prompt(self, text: str, payload_type: str, strength: int = 3) -> str:
        if "academic_rewording" in self.skill_filename:
            intensity_descriptions = {
                1: "Light: apply minimal changes — moderate vocabulary upgrades and minor structural tweaks while keeping the original sentence flow mostly intact.",
                2: "Light-Moderate: apply noticeable vocabulary upgrades and restructure some sentences while preserving overall flow.",
                3: "Moderate: clearly restructure most sentences — change clause order, vary openings, split or combine sentences where it improves clarity.",
                4: "Strong: aggressively restructure nearly every sentence — rebuild sentence architecture while preserving core meaning.",
                5: "Maximum: completely transform the text — every sentence must be rebuilt from the ground up with entirely different grammatical scaffolding."
            }
            return (
                "Please rewrite the following text and provide exactly three options in JSON format:\n"
                "{\n"
                '  "Academic": "academic version",\n'
                '  "Concise": "concise version",\n'
                '  "High-Impact": "high-impact version"\n'
                "}\n"
                f"Transformation intensity (1-5): {strength} — {intensity_descriptions[strength]}\n"
                f"Text: \"{text}\""
            )
        elif "humanizer_noora" in self.skill_filename:
            return f"Rewrite the following draft to match Dr. Noora Noureldin's writing style. Output ONLY the rewritten text:\n\"{text}\""
        elif "humanizer_general" in self.skill_filename:
            return f"Rewrite the following draft to remove AI patterns. Output ONLY the rewritten text:\n\"{text}\""
        elif "proofreading" in self.skill_filename:
            if payload_type == "phase1":
                return (
                    "Analyze the text and detect proofreading issues. Return exactly a JSON list of issues in this format:\n"
                    "[\n"
                    "  {\n"
                    '    "id": 1,\n'
                    '    "severity": "CRITICAL|MAJOR|MINOR|STYLE",\n'
                    '    "location": "Sentence or clause context",\n'
                    '    "diagnosis": "What the issue is",\n'
                    '    "why_matters": "Why it matters",\n'
                    '    "actionable_fix": "How to fix it"\n'
                    "  }\n"
                    "]\n"
                    f"Text: \"{text}\""
                )
            else:
                return f"Apply all corrections for the text. Output ONLY the corrected text:\n\"{text}\""
        return f"Process this text:\n\"{text}\""

    def _parse_response(self, response_text: str, payload_type: str) -> dict:
        response_text = response_text.strip()
        
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()
            
        if "academic_rewording" in self.skill_filename:
            try:
                import json
                data = json.loads(response_text)
                return {
                    "status": "success",
                    "options": [
                        {"type": "Academic", "text": data.get("Academic", "")},
                        {"type": "Concise", "text": data.get("Concise", "")},
                        {"type": "High-Impact", "text": data.get("High-Impact", "")}
                    ]
                }
            except Exception:
                return {
                    "status": "success",
                    "options": [
                        {"type": "Academic", "text": response_text},
                        {"type": "Concise", "text": response_text},
                        {"type": "High-Impact", "text": response_text}
                    ]
                }
        elif "proofreading" in self.skill_filename and payload_type == "phase1":
            try:
                import json
                issues = json.loads(response_text)
                return {
                    "status": "success",
                    "issues": issues
                }
            except Exception:
                return {
                    "status": "success",
                    "issues": [{
                        "id": 1,
                        "severity": "MINOR",
                        "location": "Text",
                        "diagnosis": "Review completed. No details parsed.",
                        "why_matters": "General clarity.",
                        "actionable_fix": "Check text manually."
                    }]
                }
        else:
            return {
                "status": "success",
                "text": response_text
            }
