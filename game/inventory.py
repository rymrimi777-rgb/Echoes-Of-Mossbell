"""
Inventory system – item database with real 16x16 pixel icons, categories, and usable items.
"""
import os, pygame
from game.settings import ITEM_DIR, COLOR_LIGHTEST, COLOR_DARKEST


class Item:
    def __init__(self, item_id, name, category, description, icon_file,
                 stackable=True, consumable=False, heal=0):
        self.item_id = item_id
        self.name = name
        self.category = category       # "Items", "Gear", "Keys"
        self.description = description
        self.icon_file = icon_file     # relative path inside assets/items
        self.stackable = stackable
        self.consumable = consumable
        self.heal = heal
        self._cached_icon = None

    def get_icon(self):
        if self._cached_icon is not None:
            return self._cached_icon

        path = os.path.join(ITEM_DIR, self.icon_file)
        if os.path.isfile(path):
            self._cached_icon = pygame.image.load(path).convert_alpha()
        else:
            s = pygame.Surface((16, 16))
            s.fill(COLOR_LIGHTEST)
            pygame.draw.rect(s, COLOR_DARKEST, (2, 2, 12, 12), 1)
            self._cached_icon = s
        return self._cached_icon


# ---- Master Item Catalog ---------------------------------------------------
ITEMS = {
    # --- Consumables & Food ---
    "potion": Item(
        "potion", "Healing Potion", "Items",
        "A revitalizing draught. Restores 20 HP.",
        "consumables_potions/consumables_potions_000.png",
        consumable=True, heal=20
    ),
    "elixir": Item(
        "elixir", "Magic Elixir", "Items",
        "Rare ancient blend. Restores 50 HP fully.",
        "consumables_potions/consumables_potions_002.png",
        consumable=True, heal=50
    ),
    "apple": Item(
        "apple", "Sweet Apple", "Items",
        "Freshly picked in Mossbell. Restores 10 HP.",
        "food/food_000.png",
        consumable=True, heal=10
    ),
    "bread": Item(
        "bread", "Travel Bread", "Items",
        "Hearty travel bread. Restores 15 HP.",
        "food/food_002.png",
        consumable=True, heal=15
    ),
    "herb": Item(
        "herb", "Forest Herb", "Items",
        "Medicinal fragrant herb from Whispering Woods.",
        "herbs/herbs_000.png"
    ),
    "glow_herb": Item(
        "glow_herb", "Glow Herb", "Items",
        "Rare luminescent flora found in deep caverns.",
        "herbs/herbs_002.png"
    ),
    "mushroom": Item(
        "mushroom", "Glow Mushroom", "Items",
        "Bioluminescent fungus. Radiates a faint aura.",
        "food/food_005.png"
    ),

    # --- Equipment & Gear ---
    "sword": Item(
        "sword", "Iron Sword", "Gear",
        "Forged blade of the village watch.",
        "weapons_swords/weapons_swords_000.png",
        stackable=False
    ),
    "shield": Item(
        "shield", "Oak Shield", "Gear",
        "Reinforced wooden shield with metal rim.",
        "armour_shields/armour_shields_000.png",
        stackable=False
    ),
    "armor": Item(
        "armor", "Leather Vest", "Gear",
        "Flexible boiled leather protective tunic.",
        "armour_body/armour_body_000.png",
        stackable=False
    ),
    "helmet": Item(
        "helmet", "Iron Cap", "Gear",
        "Sturdy steel cap worn by ancient guards.",
        "armour_helmets/armour_helmets_000.png",
        stackable=False
    ),

    # --- Keys, Gems & Relics ---
    "old_key": Item(
        "old_key", "Old Key", "Keys",
        "A tarnished iron key. Unlocks ancient doors.",
        "keys/keys_000.png",
        stackable=False
    ),
    "gold_key": Item(
        "gold_key", "Golden Key", "Keys",
        "Ornate key from the Elder's personal archive.",
        "keys/keys_002.png",
        stackable=False
    ),
    "ring": Item(
        "ring", "Silver Ring", "Keys",
        "Timmy's mother's treasured silver ring.",
        "jewellery_rings/jewellery_rings_000.png",
        stackable=False
    ),
    "amulet": Item(
        "amulet", "Sun Amulet", "Keys",
        "Sacred pendant that dispels dark illusions.",
        "jewellery_amulets/jewellery_amulets_000.png",
        stackable=False
    ),
    "crystal": Item(
        "crystal", "Shadow Crystal", "Keys",
        "Pulses with dark energy. Key to the curse.",
        "gems/gems_000.png",
        stackable=False
    ),
    "coins": Item(
        "coins", "Gold Coins", "Keys",
        "Ancient mint coins found in the dungeon.",
        "coins/coins_000.png",
        stackable=True
    ),
    "torn_page": Item(
        "torn_page", "Torn Journal", "Keys",
        "Page from a traveler's journal describing a grotto.",
        "books/books_000.png",
        stackable=False
    ),
    "map_piece": Item(
        "map_piece", "Dungeon Map", "Keys",
        "Chart of the catacombs beneath the watchtower.",
        "misc/misc_000.png",
        stackable=False
    ),
}


class Inventory:
    """Manages player item storage, categories, and usage."""

    CATEGORIES = ["Items", "Gear", "Keys"]

    def __init__(self):
        self.items = {}  # item_id -> quantity

    def add(self, item_id, qty=1):
        if item_id not in ITEMS:
            return False
        self.items[item_id] = self.items.get(item_id, 0) + qty
        return True

    def remove(self, item_id, qty=1):
        if item_id not in self.items:
            return False
        self.items[item_id] -= qty
        if self.items[item_id] <= 0:
            del self.items[item_id]
        return True

    def has(self, item_id, qty=1):
        return self.items.get(item_id, 0) >= qty

    def get_count(self, item_id):
        return self.items.get(item_id, 0)

    def get_by_category(self, category):
        """Return list of (Item, qty) in given category."""
        result = []
        for iid, qty in self.items.items():
            if iid in ITEMS and ITEMS[iid].category == category:
                result.append((ITEMS[iid], qty))
        return result

    def get_all(self):
        """Return all items."""
        result = []
        for iid, qty in self.items.items():
            if iid in ITEMS:
                result.append((ITEMS[iid], qty))
        return result

    def to_dict(self):
        return dict(self.items)

    def from_dict(self, d):
        self.items = dict(d)
