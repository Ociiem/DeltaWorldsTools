# Canonical ActiveWorlds / DeltaWorlds bone names and common aliases.
# Two AW styles exist:
#   Classic SEQ:  aw_lfshoulder, aw_rtshoulder, aw_lfhip, ...
#   Delta CAV:    aw_shoulderl,  aw_shoulderr,  aw_hipl,  ...
# Both are accepted as already-correct. Suggestions prefer classic lf/rt.

# Each entry: (canonical_suggestion, [already-ok names], [source patterns to match])
# Sources are matched after normalization. More specific patterns should appear
# BEFORE more generic ones so they win (we score by match quality + length).

AW_BONE_DEFS = [
    # --- Core / spine chain (Bip01 Spine, Spine1, Spine2) ---
    # Order matters for suggestions: Spine → spine0, Spine1 → back, Spine2 → back2
    ("aw_spine0",
     ["aw_spine0", "spine0"],
     ["spine0", "spine_00", "spine00"]),
    ("aw_back",
     ["aw_back", "aw_spine1", "back", "spine1"],
     ["spine1", "spine_01", "spine01"]),
    ("aw_back2",
     ["aw_back2", "aw_spine2", "spine2"],
     ["spine2", "spine_02", "spine02", "upperchest"]),
    # Generic "spine" (no number) → aw_spine0 (first spine)
    ("aw_spine0",
     ["aw_spine0", "aw_spine"],
     ["spine"]),
    ("aw_pelvis",
     ["aw_pelvis", "pelvis"],
     ["pelvis", "hips", "hip", "root"]),
    ("aw_neck",
     ["aw_neck", "neck"],
     ["neck", "neck_01", "neck01"]),
    ("aw_neck2",
     ["aw_neck2", "neck2"],
     ["neck2", "neck_02", "neck02"]),
    ("aw_head",
     ["aw_head", "head"],
     ["head"]),

    # --- Left arm ---
    ("aw_lfsternum",
     ["aw_lfsternum", "aw_sternuml", "lfsternum", "sternuml"],
     ["leftshoulder", "l_clavicle", "clavicle_l", "l_clavicle", "shoulder_l"]),
    ("aw_lfshoulder",
     ["aw_lfshoulder", "aw_lfshuolder", "aw_shoulderl", "lfshoulder", "shoulderl"],
     ["leftarm", "left_arm", "leftupperarm", "l_upperarm", "upperarm_l", "upper_arm_l",
      "bicep_l", "leftbicep", "left_bicep", "l_bicep", "l_arm"]),
    ("aw_lfelbow",
     ["aw_lfelbow", "aw_elbowl", "lfelbow", "elbowl"],
     ["leftforearm", "left_forearm", "l_forearm", "lowerarm_l", "forearm_l", "lower_arm_l"]),
    ("aw_lfwrist",
     ["aw_lfwrist", "aw_wristl", "lfwrist", "wristl"],
     ["lefthand", "left_hand", "l_hand", "hand_l", "wrist_l"]),
    ("aw_lffingers",
     ["aw_lffingers", "lffingers"],
     ["leftfingers", "l_fingers", "fingers_l"]),

    # --- Right arm ---
    ("aw_rtsternum",
     ["aw_rtsternum", "aw_sternumr", "rtsternum", "sternumr"],
     ["rightshoulder", "r_clavicle", "clavicle_r", "shoulder_r"]),
    ("aw_rtshoulder",
     ["aw_rtshoulder", "aw_shoulderr", "rtshoulder", "shoulderr"],
     ["rightarm", "right_arm", "rightupperarm", "r_upperarm", "upperarm_r", "upper_arm_r",
      "bicep_r", "rightbicep", "right_bicep", "r_bicep", "r_arm"]),
    ("aw_rtelbow",
     ["aw_rtelbow", "aw_elbowr", "rtelbow", "elbowr"],
     ["rightforearm", "right_forearm", "r_forearm", "lowerarm_r", "forearm_r", "lower_arm_r"]),
    ("aw_rtwrist",
     ["aw_rtwrist", "aw_wristr", "rtwrist", "wristr"],
     ["righthand", "right_hand", "r_hand", "hand_r", "wrist_r"]),
    ("aw_rtfingers",
     ["aw_rtfingers", "rtfingers"],
     ["rightfingers", "r_fingers", "fingers_r"]),

    # --- Left leg ---
    ("aw_lfhip",
     ["aw_lfhip", "aw_hipl", "lfhip", "hipl"],
     ["leftupleg", "left_upleg", "leftthigh", "l_thigh", "thigh_l", "upper_leg_l", "hip_l", "l_hip"]),
    ("aw_lfknee",
     ["aw_lfknee", "aw_kneel", "lfknee", "kneel"],
     ["leftleg", "left_leg", "leftcalf", "l_calf", "calf_l", "lower_leg_l", "shin_l", "knee_l"]),
    ("aw_lfankle",
     ["aw_lfankle", "aw_anklel", "lfankle", "anklel"],
     ["leftfoot", "left_foot", "l_foot", "foot_l", "ankle_l"]),
    ("aw_lftoes",
     ["aw_lftoes", "aw_toesl", "lftoes", "toesl"],
     ["lefttoe", "left_toe", "lefttoebase", "l_toe", "ball_l", "toe_l", "toe0_l"]),

    # --- Right leg ---
    ("aw_rthip",
     ["aw_rthip", "aw_hipr", "rthip", "hipr"],
     ["rightupleg", "right_upleg", "rightthigh", "r_thigh", "thigh_r", "upper_leg_r", "hip_r", "r_hip"]),
    ("aw_rtknee",
     ["aw_rtknee", "aw_kneer", "rtknee", "kneer"],
     ["rightleg", "right_leg", "rightcalf", "r_calf", "calf_r", "lower_leg_r", "shin_r", "knee_r"]),
    ("aw_rtankle",
     ["aw_rtankle", "aw_ankler", "rtankle", "ankler"],
     ["rightfoot", "right_foot", "r_foot", "foot_r", "ankle_r"]),
    ("aw_rttoes",
     ["aw_rttoes", "aw_toesr", "rttoes", "toesr"],
     ["righttoe", "right_toe", "righttoebase", "r_toe", "ball_r", "toe_r", "toe0_r"]),

    # --- Fingers (Bip01: Finger0=thumb, Finger1=index, Finger2=middle, Finger3=ring, Finger4=pinky)
    # second digit in name = joint index (0/blank = proximal, 1 = mid, 2 = tip)
    # Left thumb (digit 1) — Mixamo: LeftHandThumb1/2/3
    ("aw_lf1finger1",
     ["aw_lf1finger1", "aw_1finger1l"],
     ["l_finger0", "finger0_l", "l_thumb", "thumb_l", "l_finger_0",
      "lefthandthumb1", "left_hand_thumb_1", "handthumb1_l", "l_thumb1"]),
    ("aw_lf1finger2",
     ["aw_lf1finger2", "aw_1finger2l"],
     ["l_finger01", "finger01_l", "l_finger_01", "l_thumb2",
      "lefthandthumb2", "left_hand_thumb_2", "handthumb2_l", "thumb2_l"]),
    ("aw_lf1finger3",
     ["aw_lf1finger3", "aw_1finger3l"],
     ["l_finger02", "finger02_l", "l_finger_02", "l_thumb3",
      "lefthandthumb3", "left_hand_thumb_3", "handthumb3_l", "thumb3_l"]),
    ("aw_lf2finger1",
     ["aw_lf2finger1", "aw_2finger1l"],
     ["l_finger1", "finger1_l", "l_finger_1", "l_index",
      "lefthandindex1", "left_hand_index_1", "handindex1_l", "index1_l", "l_index1"]),
    ("aw_lf2finger2",
     ["aw_lf2finger2", "aw_2finger2l"],
     ["l_finger11", "finger11_l", "l_finger_11",
      "lefthandindex2", "left_hand_index_2", "handindex2_l", "index2_l", "l_index2"]),
    ("aw_lf2finger3",
     ["aw_lf2finger3", "aw_2finger3l"],
     ["l_finger12", "finger12_l", "l_finger_12",
      "lefthandindex3", "left_hand_index_3", "handindex3_l", "index3_l", "l_index3"]),
    ("aw_lf3finger1",
     ["aw_lf3finger1", "aw_3finger1l"],
     ["l_finger2", "finger2_l", "l_finger_2", "l_middle",
      "lefthandmiddle1", "left_hand_middle_1", "handmiddle1_l", "middle1_l", "l_middle1"]),
    ("aw_lf3finger2",
     ["aw_lf3finger2", "aw_3finger2l"],
     ["l_finger21", "finger21_l", "l_finger_21",
      "lefthandmiddle2", "left_hand_middle_2", "handmiddle2_l", "middle2_l", "l_middle2"]),
    ("aw_lf3finger3",
     ["aw_lf3finger3", "aw_3finger3l"],
     ["l_finger22", "finger22_l", "l_finger_22",
      "lefthandmiddle3", "left_hand_middle_3", "handmiddle3_l", "middle3_l", "l_middle3"]),
    ("aw_lf4finger1",
     ["aw_lf4finger1", "aw_4finger1l"],
     ["l_finger3", "finger3_l", "l_finger_3", "l_ring",
      "lefthandring1", "left_hand_ring_1", "handring1_l", "ring1_l", "l_ring1"]),
    ("aw_lf4finger2",
     ["aw_lf4finger2", "aw_4finger2l"],
     ["l_finger31", "finger31_l", "l_finger_31",
      "lefthandring2", "left_hand_ring_2", "handring2_l", "ring2_l", "l_ring2"]),
    ("aw_lf4finger3",
     ["aw_lf4finger3", "aw_4finger3l"],
     ["l_finger32", "finger32_l", "l_finger_32",
      "lefthandring3", "left_hand_ring_3", "handring3_l", "ring3_l", "l_ring3"]),
    ("aw_lf5finger1",
     ["aw_lf5finger1", "aw_5finger1l"],
     ["l_finger4", "finger4_l", "l_finger_4", "l_pinky",
      "lefthandpinky1", "left_hand_pinky_1", "handpinky1_l", "pinky1_l", "l_pinky1"]),
    ("aw_lf5finger2",
     ["aw_lf5finger2", "aw_5finger2l"],
     ["l_finger41", "finger41_l", "l_finger_41",
      "lefthandpinky2", "left_hand_pinky_2", "handpinky2_l", "pinky2_l", "l_pinky2"]),
    ("aw_lf5finger3",
     ["aw_lf5finger3", "aw_5finger3l"],
     ["l_finger42", "finger42_l", "l_finger_42",
      "lefthandpinky3", "left_hand_pinky_3", "handpinky3_l", "pinky3_l", "l_pinky3"]),
    ("aw_rt1finger1",
     ["aw_rt1finger1", "aw_1finger1r"],
     ["r_finger0", "finger0_r", "r_thumb", "thumb_r", "r_finger_0",
      "righthandthumb1", "right_hand_thumb_1", "handthumb1_r", "r_thumb1"]),
    ("aw_rt1finger2",
     ["aw_rt1finger2", "aw_1finger2r"],
     ["r_finger01", "finger01_r", "r_finger_01",
      "righthandthumb2", "right_hand_thumb_2", "handthumb2_r", "thumb2_r", "r_thumb2"]),
    ("aw_rt1finger3",
     ["aw_rt1finger3", "aw_1finger3r"],
     ["r_finger02", "finger02_r", "r_finger_02",
      "righthandthumb3", "right_hand_thumb_3", "handthumb3_r", "thumb3_r", "r_thumb3"]),
    ("aw_rt2finger1",
     ["aw_rt2finger1", "aw_2finger1r"],
     ["r_finger1", "finger1_r", "r_finger_1", "r_index",
      "righthandindex1", "right_hand_index_1", "handindex1_r", "index1_r", "r_index1"]),
    ("aw_rt2finger2",
     ["aw_rt2finger2", "aw_2finger2r"],
     ["r_finger11", "finger11_r", "r_finger_11",
      "righthandindex2", "right_hand_index_2", "handindex2_r", "index2_r", "r_index2"]),
    ("aw_rt2finger3",
     ["aw_rt2finger3", "aw_2finger3r"],
     ["r_finger12", "finger12_r", "r_finger_12",
      "righthandindex3", "right_hand_index_3", "handindex3_r", "index3_r", "r_index3"]),
    ("aw_rt3finger1",
     ["aw_rt3finger1", "aw_3finger1r"],
     ["r_finger2", "finger2_r", "r_finger_2", "r_middle",
      "righthandmiddle1", "right_hand_middle_1", "handmiddle1_r", "middle1_r", "r_middle1"]),
    ("aw_rt3finger2",
     ["aw_rt3finger2", "aw_3finger2r"],
     ["r_finger21", "finger21_r", "r_finger_21",
      "righthandmiddle2", "right_hand_middle_2", "handmiddle2_r", "middle2_r", "r_middle2"]),
    ("aw_rt3finger3",
     ["aw_rt3finger3", "aw_3finger3r"],
     ["r_finger22", "finger22_r", "r_finger_22",
      "righthandmiddle3", "right_hand_middle_3", "handmiddle3_r", "middle3_r", "r_middle3"]),
    ("aw_rt4finger1",
     ["aw_rt4finger1", "aw_4finger1r"],
     ["r_finger3", "finger3_r", "r_finger_3", "r_ring",
      "righthandring1", "right_hand_ring_1", "handring1_r", "ring1_r", "r_ring1"]),
    ("aw_rt4finger2",
     ["aw_rt4finger2", "aw_4finger2r"],
     ["r_finger31", "finger31_r", "r_finger_31",
      "righthandring2", "right_hand_ring_2", "handring2_r", "ring2_r", "r_ring2"]),
    ("aw_rt4finger3",
     ["aw_rt4finger3", "aw_4finger3r"],
     ["r_finger32", "finger32_r", "r_finger_32",
      "righthandring3", "right_hand_ring_3", "handring3_r", "ring3_r", "r_ring3"]),
    ("aw_rt5finger1",
     ["aw_rt5finger1", "aw_5finger1r"],
     ["r_finger4", "finger4_r", "r_finger_4", "r_pinky",
      "righthandpinky1", "right_hand_pinky_1", "handpinky1_r", "pinky1_r", "r_pinky1"]),
    ("aw_rt5finger2",
     ["aw_rt5finger2", "aw_5finger2r"],
     ["r_finger41", "finger41_r", "r_finger_41",
      "righthandpinky2", "right_hand_pinky_2", "handpinky2_r", "pinky2_r", "r_pinky2"]),
    ("aw_rt5finger3",
     ["aw_rt5finger3", "aw_5finger3r"],
     ["r_finger42", "finger42_r", "r_finger_42",
      "righthandpinky3", "right_hand_pinky_3", "handpinky3_r", "pinky3_r", "r_pinky3"]),

    # --- Face ---
    ("aw_lfeye",
     ["aw_lfeye", "aw_eyel", "lfeye", "eyel"],
     ["lefteye", "left_eye", "eye_l", "l_eye", "leye"]),
    ("aw_rteye",
     ["aw_rteye", "aw_eyer", "rteye", "eyer"],
     ["righteye", "right_eye", "eye_r", "r_eye", "reye"]),
    ("aw_lflid",
     ["aw_lflid", "aw_lidl", "lflid", "lidl"],
     ["l_eyeblinktop", "eyeblinktop_l", "l_eyelid", "eyelid_l", "l_eyeblink", "leyeblinktop"]),
    ("aw_rtlid",
     ["aw_rtlid", "aw_lidr", "rtlid", "lidr"],
     ["r_eyeblinktop", "eyeblinktop_r", "r_eyelid", "eyelid_r", "r_eyeblink", "reyeblinktop"]),
    ("aw_lfear",
     ["aw_lfear", "aw_earl", "lfear", "earl"],
     ["leftear", "left_ear", "ear_l", "l_ear"]),
    ("aw_rtear",
     ["aw_rtear", "aw_earr", "rtear", "earr"],
     ["rightear", "right_ear", "ear_r", "r_ear"]),
    ("aw_lfbreast",
     ["aw_lfbreast", "aw_breastl", "lfbreast", "breastl"],
     ["leftbreast", "breast_l", "l_breast"]),
    ("aw_rtbreast",
     ["aw_rtbreast", "aw_breastr", "rtbreast", "breastr"],
     ["rightbreast", "breast_r", "r_breast"]),
    ("aw_nose",
     ["aw_nose", "nose"],
     ["nose"]),
    ("aw_mandible",
     ["aw_mandible", "mandible"],
     ["mjaw", "jaw", "mandible", "m_jaw"]),
    ("aw_chin",
     ["aw_chin", "chin"],
     ["chin", "mchin"]),
    ("aw_liplower",
     ["aw_liplower", "liplower"],
     ["mbottomlip", "m_bottomlip", "bottomlip", "lowerlip", "m_lowerlip"]),
    ("aw_lipupper",
     ["aw_lipupper", "lipupper"],
     ["mupperlip", "m_upperlip", "upperlip", "m_toplip"]),
    ("aw_lfliplower",
     ["aw_lfliplower", "lfliplower"],
     ["l_mouthbottom", "mouthbottom_l", "l_bottomlip", "l_lowerlip", "lmouthbottom"]),
    ("aw_rtliplower",
     ["aw_rtliplower", "rtliplower"],
     ["r_mouthbottom", "mouthbottom_r", "r_bottomlip", "r_lowerlip", "rmouthbottom"]),
    ("aw_lflipupper",
     ["aw_lflipupper", "lflipupper"],
     ["l_mouthtop", "mouthtop_l", "l_upperlip", "l_toplip", "upperlip_l",
      "lupperlip", "leftupperlip", "left_upperlip"]),
    ("aw_rtlipupper",
     ["aw_rtlipupper", "rtlipupper"],
     ["r_mouthtop", "mouthtop_r", "r_upperlip", "r_toplip", "upperlip_r",
      "rupperlip", "rightupperlip", "right_upperlip"]),
    ("aw_lfcheek",
     ["aw_lfcheek", "aw_cheekl", "lfcheek", "cheekl"],
     ["l_cheek", "cheek_l", "leftcheek", "lcheek"]),
    ("aw_rtcheek",
     ["aw_rtcheek", "aw_cheekr", "rtcheek", "cheekr"],
     ["r_cheek", "cheek_r", "rightcheek", "rcheek"]),
    ("aw_lfbrow",
     ["aw_lfbrow", "aw_browl", "lfbrow", "browl"],
     ["l_innereyebrow", "innereyebrow_l", "linnereyebrow", "l_eyebrow", "eyebrow_l",
      "l_brow", "lbrow", "l_innereye_brow", "linner_eyebrow", "innereyebrow"]),
    ("aw_rtbrow",
     ["aw_rtbrow", "aw_browr", "rtbrow", "browr"],
     ["r_innereyebrow", "innereyebrow_r", "rinnereyebrow", "r_eyebrow", "eyebrow_r",
      "r_brow", "rbrow", "r_innereye_brow", "rinner_eyebrow"]),
    ("aw_lfbrowouter",
     ["aw_lfbrowouter", "aw_browouterl", "lfbrowouter", "browouterl"],
     ["l_outereyebrow", "outereyebrow_l", "l_outer_eyebrow", "louter_eyebrow", "loutereyebrow"]),
    ("aw_rtbrowouter",
     ["aw_rtbrowouter", "aw_browouterr", "rtbrowouter", "browouterr"],
     ["r_outereyebrow", "outereyebrow_r", "r_outer_eyebrow", "router_eyebrow", "routereyebrow"]),
        ("aw_lips",
     ["aw_lips", "lips"],
     ["lips"]),  # exact only — not mouthcorner / mouthbottom / etc.

    # --- Tail / props / hair ---
    ("aw_tail",
     ["aw_tail", "tail"],
     ["tail", "tail1", "tail_01"]),
    ("aw_tail2",
     ["aw_tail2", "tail2"],
     ["tail2", "tail_02"]),
    ("aw_tail3",
     ["aw_tail3", "tail3"],
     ["tail3", "tail_03"]),
    ("aw_tail4",
     ["aw_tail4", "tail4"],
     ["tail4", "tail_04"]),
    ("aw_obj",
     ["aw_obj", "aw_obj1", "obj", "obj1"],
     ["obj", "obj1", "prop", "prop1", "attachment"]),
    ("aw_obj2",
     ["aw_obj2", "obj2"],
     ["obj2", "prop2"]),
    ("aw_obj3",
     ["aw_obj3", "obj3"],
     ["obj3", "prop3"]),
    ("aw_hair",
     ["aw_hair", "hair"],
     ["hair", "hair1"]),
    ("aw_hair2",
     ["aw_hair2", "hair2"],
     ["hair2"]),
    ("aw_hair3",
     ["aw_hair3", "hair3"],
     ["hair3"]),
    ("aw_hair4",
     ["aw_hair4", "hair4"],
     ["hair4"]),
]


_OBJ_KEYWORDS = (
    "ribbon", "bow", "weapon", "sword", "gun", "knife", "blade", "shield",
    "bag", "pouch", "backpack", "pack", "cape", "cloak", "scarf", "shawl",
    "belt", "buckle", "jewelry", "jewellery", "jewel", "necklace", "pendant",
    "bracelet", "earring", "earing", "glasses", "goggle", "mask",
    "prop", "attach", "accessory", "extra", "item", "object", "obj",
    "wing", "tail", "skirt", "banner", "flag", "holster", "quiver", "sheath",
    "book", "scroll", "lantern", "torch", "pipe", "guitar", "phone", "camera",
)
_HAIR_KEYWORDS = (
    "hair", "bang", "bangs", "ponytail", "pigtail", "braid", "bun", "fringe",
    "horn", "horns", "antler", "antenna", "feather", "plume",
    "hat", "helmet", "cap", "crown", "tiara", "bandana", "bandanna", "headband",
    "hood", "veil", "wig", "mohawk", "dread", "beard", "mustache", "moustache",
    "headtop", "head_top", "top_end", "head_end",
)
_SKIP_ACCESSORY = (
    "twist", "roll", "corrective", "correct", "kinematic", "kinetik", "muscle",
    "helper", "ik_", "_ik", "fk_", "_fk", "nurb", "spline", "target", "pole",
    "metacarpal", "meta_", "driver", "control", "ctrl", "weight", "leaf",
    "end_site", "endsite", "nub", "dummy", "null", "socket",
)


def _norm_name(name):
    """Lowercase, unify separators, strip common rig prefixes."""
    import re
    n = name.lower().strip()
    for ch in " :.-":
        n = n.replace(ch, "_")
    while "__" in n:
        n = n.replace("__", "_")
    n = n.strip("_")
    for pref in (
        "mixamorig_", "mixamo_", "bip001_", "bip01_", "bip_01_", "bip_",
        "c_", "def_", "org_", "ctrl_", "drv_", "rb_", "sk_",
    ):
        if n.startswith(pref):
            n = n[len(pref):]
    n = re.sub(
        r"^(left|right)_?hand_?(thumb|index|middle|ring|pinky)_?(\d+)$",
        lambda m: m.group(1) + "hand" + m.group(2) + m.group(3),
        n,
    )
    n = re.sub(
        r"^([lr])(inner|outer)?(eye|ear|arm|hand|foot|leg|thigh|calf|forearm|upperarm|shoulder|clavicle|breast|hip|knee|ankle|toe|finger|cheek|brow|mouth|eyelid|eyeblink|eyebrow)",
        lambda m: m.group(1) + "_" + (m.group(2) or "") + m.group(3), n)
    n = n.replace("__", "_")
    n = re.sub(
        r"(eye|ear|arm|hand|foot|leg|thigh|calf|forearm|upperarm|shoulder|clavicle|breast|hip|knee|ankle|toe|finger|cheek|brow)([lr])$",
        r"\1_\2", n)
    return n.strip("_")


def _is_already_aw(bone_name):
    return bone_name.lower().strip().startswith("aw_")


def _is_skip_accessory(n):
    return any(s in n for s in _SKIP_ACCESSORY)


def _accessory_score(bone_name):
    import re
    n = _norm_name(bone_name)
    if _is_skip_accessory(n):
        return None
    num = 0
    m = re.search(r"(\d+)$", n)
    if m:
        num = int(m.group(1))
    hair_hits = sum(1 for k in _HAIR_KEYWORDS if k in n)
    obj_hits = sum(1 for k in _OBJ_KEYWORDS if k in n)
    is_headish = (
        ("head" in n and n not in ("head",) and not n.endswith("_head"))
        or "headtop" in n
        or (n.endswith("_end") and "head" in n)
    )
    if hair_hits and hair_hits >= obj_hits:
        return ("hair", 50 + hair_hits * 10 + (5 if num else 0), (num or 99, n))
    if obj_hits:
        return ("obj", 50 + obj_hits * 10 + (5 if num else 0), (num or 99, n))
    if is_headish:
        return ("hair", 30, (num or 99, n))
    if num and not any(x in n for x in (
        "spine", "finger", "toe", "arm", "leg", "thigh", "calf", "neck",
        "breast", "eye", "ear", "lip", "brow", "cheek", "jaw", "mouth",
    )):
        return ("obj", 20, (num, n))
    return None


def suggest_aw_name(bone_name, used_targets=None):
    """Body/face match only (accessories via assign_accessories / build_suggestions)."""
    used_targets = used_targets or set()
    n = _norm_name(bone_name)
    if _is_already_aw(bone_name):
        return ("", "already AW-compatible")
    candidates = []
    accessory_slots = {
        "aw_obj", "aw_obj2", "aw_obj3",
        "aw_hair", "aw_hair2", "aw_hair3", "aw_hair4",
    }
    for canonical, _aliases, sources in AW_BONE_DEFS:
        if canonical in accessory_slots or canonical in used_targets:
            continue
        for s in sources:
            sn = _norm_name(s)
            if not sn:
                continue
            if n == sn:
                candidates.append((100, len(sn), canonical))
            elif n.endswith("_" + sn) or n.startswith(sn + "_"):
                if len(sn) >= 3:
                    candidates.append((80, len(sn), canonical))
            elif sn in n and len(sn) >= 4:
                # Don't let "head" match HeadTop_End
                if sn == "head" and n != "head" and not n.endswith("_head"):
                    continue
                candidates.append((50, len(sn), canonical))
    if candidates:
        candidates.sort(key=lambda x: (-x[0], -x[1]))
        return (candidates[0][2], "matched")
    return ("", "no suggestion")


def assign_accessories(unassigned_names, used_targets):
    used = set(used_targets)
    result = {}
    scored = []
    for name in unassigned_names:
        info = _accessory_score(name)
        if info is None:
            continue
        kind, score, sort_key = info
        scored.append((kind, -score, sort_key, name))
    scored.sort()
    obj_slots = [s for s in ("aw_obj", "aw_obj2", "aw_obj3") if s not in used]
    hair_slots = [s for s in ("aw_hair", "aw_hair2", "aw_hair3", "aw_hair4") if s not in used]

    # 1) Explicit obj keywords → obj slots (numbered chains first via sort)
    for kind, _, _, name in scored:
        if kind == "obj" and obj_slots and name not in result:
            slot = obj_slots.pop(0)
            result[name] = slot
            used.add(slot)
    # 2) Any remaining accessories (incl. head-ish / weak obj) fill leftover obj slots
    #    before hair — e.g. HeadTop_End → aw_obj3 when ribbons took obj/obj2
    for kind, _, _, name in scored:
        if name in result or not obj_slots:
            continue
        slot = obj_slots.pop(0)
        result[name] = slot
        used.add(slot)
    # 3) Remaining → hair slots
    for kind, _, _, name in scored:
        if name in result or not hair_slots:
            continue
        slot = hair_slots.pop(0)
        result[name] = slot
        used.add(slot)
    return result


def build_suggestions(bone_names):
    """Two-pass: body/face, then accessories. Returns [(name, sug, status), ...]."""
    used = set()
    for name in bone_names:
        if name.lower().startswith("aw_"):
            used.add(name.lower())
            for can, aliases, _ in AW_BONE_DEFS:
                n = _norm_name(name)
                accepted = {_norm_name(can)} | {_norm_name(a) for a in aliases}
                if n in accepted:
                    used.add(can)

    primary = {}
    unassigned = []
    for name in bone_names:
        if name.lower().startswith("aw_"):
            primary[name] = ("", "OK")
            continue
        sug, reason = suggest_aw_name(name, used)
        if sug:
            primary[name] = (sug, "suggest")
            used.add(sug)
        else:
            unassigned.append(name)
            primary[name] = ("", "blank")

    for name, slot in assign_accessories(unassigned, used).items():
        primary[name] = (slot, "suggest")
        used.add(slot)

    return [(name, primary[name][0], primary[name][1]) for name in bone_names]
