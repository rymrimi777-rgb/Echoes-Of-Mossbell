"""
Quest / objective tracker.
"""


class Quest:
    def __init__(self, quest_id, title, description, stages):
        self.quest_id = quest_id
        self.title = title
        self.description = description
        self.stages = stages          # list of str descriptions
        self.current_stage = 0
        self.completed = False

    def advance(self):
        if self.completed:
            return
        self.current_stage += 1
        if self.current_stage >= len(self.stages):
            self.completed = True

    def stage_text(self):
        if self.completed:
            return "Completed"
        return self.stages[self.current_stage]

    def to_dict(self):
        return {"stage": self.current_stage, "completed": self.completed}

    def from_dict(self, d):
        self.current_stage = d.get("stage", 0)
        self.completed = d.get("completed", False)


# ---- Quest database ------------------------------------------------------
QUEST_DATA = {
    "main": Quest(
        "main",
        "The Vanishing",
        "People have been disappearing from Mossbell Village. Discover the truth.",
        [
            "Talk to Elder Orin in Mossbell Village.",
            "Search the Whispering Woods for clues.",
            "Find the hidden path in the deep forest.",
            "Explore the Abandoned Watchtower.",
            "Bring the Shadow Crystal to Elder Orin.",
            "Enter the Shadow Grotto and end the curse.",
        ],
    ),
    "herbs": Quest(
        "herbs",
        "Herbal Remedy",
        "Collect forest herbs for the village healer.",
        [
            "Find 3 Forest Herbs in the woods.",
            "Bring the herbs to the healer.",
        ],
    ),
    "ring": Quest(
        "ring",
        "The Lost Ring",
        "A boy in the village lost his silver ring near the old ruins.",
        [
            "Search near the ruins for a silver ring.",
            "Return the ring to the boy.",
        ],
    ),
}


class QuestManager:
    def __init__(self):
        self.quests = {}
        for qid, qdata in QUEST_DATA.items():
            self.quests[qid] = Quest(
                qdata.quest_id, qdata.title, qdata.description,
                list(qdata.stages))

    def get(self, quest_id):
        return self.quests.get(quest_id)

    def start(self, quest_id):
        q = self.quests.get(quest_id)
        if q:
            q.current_stage = 0
            q.completed = False

    def advance(self, quest_id):
        q = self.quests.get(quest_id)
        if q:
            q.advance()

    def is_at_stage(self, quest_id, stage):
        q = self.quests.get(quest_id)
        if q:
            return q.current_stage == stage and not q.completed
        return False

    def is_completed(self, quest_id):
        q = self.quests.get(quest_id)
        return q.completed if q else False

    def get_active(self):
        return [q for q in self.quests.values()
                if q.current_stage > 0 or q.completed]

    def to_dict(self):
        return {qid: q.to_dict() for qid, q in self.quests.items()}

    def from_dict(self, d):
        for qid, qd in d.items():
            if qid in self.quests:
                self.quests[qid].from_dict(qd)

