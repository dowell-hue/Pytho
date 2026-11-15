print("bonjour")
import pygame
import random
import os
import sys
import json
from enum import Enum
from dataclasses import dataclass


# ============================================================
# INITIALISATION
# ============================================================

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

CLOCK = pygame.time.Clock()


# ============================================================
# COULEURS
# ============================================================

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_GREEN = (0, 150, 0)
ORANGE = (255, 165, 0)
PURPLE = (150, 0, 200)
DARK_GRAY = (30, 30, 30)


# ============================================================
# ÉTATS DU JEU
# ============================================================

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    INVENTORY = 3
    GAME_OVER = 4


# ============================================================
# STATISTIQUES
# ============================================================

@dataclass
class Stats:
    hp: int
    max_hp: int
    attack: int
    defense: int
    level: int
    experience: int
    gold: int


# ============================================================
# PERSONNAGE
# ============================================================

class Personnage(pygame.sprite.Sprite):

    def __init__(self, x, y, nom, classe):
        super().__init__()

        self.nom = nom
        self.classe = classe

        self.x = float(x)
        self.y = float(y)

        self.width = 40
        self.height = 40

        # -----------------------------
        # STATS SELON LA CLASSE
        # -----------------------------

        if classe == "Guerrier":

            self.stats = Stats(
                hp=120,
                max_hp=120,
                attack=18,
                defense=12,
                level=1,
                experience=0,
                gold=0
            )

            self.color = BLUE

        elif classe == "Magicien":

            self.stats = Stats(
                hp=70,
                max_hp=70,
                attack=25,
                defense=5,
                level=1,
                experience=0,
                gold=0
            )

            self.color = PURPLE

        else:

            self.stats = Stats(
                hp=90,
                max_hp=90,
                attack=21,
                defense=8,
                level=1,
                experience=0,
                gold=0
            )

            self.color = ORANGE

        self.image = pygame.Surface(
            (self.width, self.height)
        )

        self.image.fill(self.color)

        self.rect = self.image.get_rect(
            topleft=(self.x, self.y)
        )

        self.speed = 5

        self.inventory = []

    # --------------------------------------------------------

    def update(self, keys):

        dx = 0
        dy = 0

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.speed

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.speed

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed

        # Empêche le déplacement diagonal d'être trop rapide
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.x += dx
        self.y += dy

        # Limites de l'écran
        self.x = max(
            0,
            min(
                self.x,
                SCREEN_WIDTH - self.width
            )
        )

        self.y = max(
            80,
            min(
                self.y,
                SCREEN_HEIGHT - self.height
            )
        )

        self.rect.topleft = (
            int(self.x),
            int(self.y)
        )

    # --------------------------------------------------------

    def take_damage(self, damage):

        actual_damage = max(
            1,
            damage - self.stats.defense // 2
        )

        self.stats.hp -= actual_damage

        if self.stats.hp < 0:
            self.stats.hp = 0

        return actual_damage

    # --------------------------------------------------------

    def heal(self, amount):

        old_hp = self.stats.hp

        self.stats.hp = min(
            self.stats.hp + amount,
            self.stats.max_hp
        )

        return self.stats.hp - old_hp

    # --------------------------------------------------------

    def gain_experience(self, amount):

        self.stats.experience += amount

        leveled_up = False

        while self.stats.experience >= self.stats.level * 100:

            needed = self.stats.level * 100

            self.stats.experience -= needed

            self.level_up()

            leveled_up = True

        return leveled_up

    # --------------------------------------------------------

    def level_up(self):

        self.stats.level += 1

        self.stats.max_hp += 20
        self.stats.hp = self.stats.max_hp

        self.stats.attack += 5
        self.stats.defense += 2

    # --------------------------------------------------------

    def add_item(self, item):

        self.inventory.append(item)

    # --------------------------------------------------------

    def draw(self, screen):

        screen.blit(
            self.image,
            self.rect
        )

        # Barre de vie

        bar_width = self.width
        bar_height = 6

        ratio = (
            self.stats.hp /
            self.stats.max_hp
        )

        fill_width = int(
            bar_width * ratio
        )

        outline = pygame.Rect(
            int(self.x),
            int(self.y) - 10,
            bar_width,
            bar_height
        )

        fill = pygame.Rect(
            int(self.x),
            int(self.y) - 10,
            fill_width,
            bar_height
        )

        pygame.draw.rect(
            screen,
            RED,
            outline
        )

        pygame.draw.rect(
            screen,
            GREEN,
            fill
        )


# ============================================================
# ENNEMI
# ============================================================

class Ennemi(pygame.sprite.Sprite):

    def __init__(self, x, y, enemy_type):

        super().__init__()

        self.x = float(x)
        self.y = float(y)

        self.width = 35
        self.height = 35

        self.enemy_type = enemy_type

        # -----------------------------
        # STATS
        # -----------------------------

        if enemy_type == "Gobelin":

            self.hp = 25
            self.max_hp = 25
            self.attack = 6
            self.defense = 1
            self.exp_reward = 30
            self.gold_reward = 10
            self.color = GREEN

        elif enemy_type == "Orc":

            self.hp = 50
            self.max_hp = 50
            self.attack = 11
            self.defense = 3
            self.exp_reward = 60
            self.gold_reward = 25
            self.color = DARK_GREEN

        else:

            self.hp = 100
            self.max_hp = 100
            self.attack = 20
            self.defense = 5
            self.exp_reward = 150
            self.gold_reward = 100
            self.color = RED

        self.image = pygame.Surface(
            (self.width, self.height)
        )

        self.image.fill(self.color)

        self.rect = self.image.get_rect(
            topleft=(self.x, self.y)
        )

        self.speed = random.uniform(0.7, 1.8)

        self.direction_x = random.choice(
            [-1, 1]
        )

        self.direction_y = random.choice(
            [-1, 1]
        )

        self.move_counter = 0

        self.move_change_interval = random.randint(
            40,
            100
        )

        # Temps avant la prochaine attaque
        self.attack_cooldown = random.randint(
            30,
            60
        )

    # --------------------------------------------------------

    def update(self):

        self.move_counter += 1

        if (
            self.move_counter >
            self.move_change_interval
        ):

            self.direction_x = random.choice(
                [-1, 1]
            )

            self.direction_y = random.choice(
                [-1, 1]
            )

            self.move_counter = 0

            self.move_change_interval = random.randint(
                40,
                100
            )

        self.x += (
            self.direction_x *
            self.speed
        )

        self.y += (
            self.direction_y *
            self.speed
        )

        # Rebond
        if (
            self.x <= 0 or
            self.x >= SCREEN_WIDTH - self.width
        ):

            self.direction_x *= -1

        if (
            self.y <= 80 or
            self.y >= SCREEN_HEIGHT - self.height
        ):

            self.direction_y *= -1

        self.x = max(
            0,
            min(
                self.x,
                SCREEN_WIDTH - self.width
            )
        )

        self.y = max(
            80,
            min(
                self.y,
                SCREEN_HEIGHT - self.height
            )
        )

        self.rect.topleft = (
            int(self.x),
            int(self.y)
        )

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    # --------------------------------------------------------

    def can_attack(self):

        return self.attack_cooldown <= 0

    # --------------------------------------------------------

    def reset_attack(self):

        self.attack_cooldown = random.randint(
            45,
            75
        )

    # --------------------------------------------------------

    def take_damage(self, damage):

        actual_damage = max(
            1,
            damage - self.defense // 2
        )

        self.hp -= actual_damage

        if self.hp < 0:
            self.hp = 0

        return actual_damage

    # --------------------------------------------------------

    def draw(self, screen):

        screen.blit(
            self.image,
            self.rect
        )

        # Barre de vie

        bar_width = self.width
        bar_height = 5

        ratio = self.hp / self.max_hp

        fill_width = int(
            bar_width * ratio
        )

        outline = pygame.Rect(
            int(self.x),
            int(self.y) - 8,
            bar_width,
            bar_height
        )

        fill = pygame.Rect(
            int(self.x),
            int(self.y) - 8,
            fill_width,
            bar_height
        )

        pygame.draw.rect(
            screen,
            RED,
            outline
        )

        pygame.draw.rect(
            screen,
            YELLOW,
            fill
        )


# ============================================================
# OBJETS
# ============================================================

class Item:

    def __init__(
        self,
        nom,
        item_type,
        valeur,
        x,
        y
    ):

        self.nom = nom
        self.type = item_type
        self.valeur = valeur

        self.x = x
        self.y = y

        self.width = 20
        self.height = 20

        self.rect = pygame.Rect(
            int(x),
            int(y),
            self.width,
            self.height
        )

        if item_type == "potion":

            self.color = RED

        elif item_type == "arme":

            self.color = ORANGE

        elif item_type == "armure":

            self.color = LIGHT_GRAY

        else:

            self.color = WHITE

    # --------------------------------------------------------

    def draw(self, screen):

        pygame.draw.rect(
            screen,
            self.color,
            self.rect
        )

        pygame.draw.rect(
            screen,
            WHITE,
            self.rect,
            2
        )


# ============================================================
# JEU
# ============================================================

class Jeu:

    def __init__(self):

        self.screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT
            )
        )

        pygame.display.set_caption(
            "RPG - Aventure Épique"
        )

        # Polices
        self.font_grande = pygame.font.Font(
            None,
            48
        )

        self.font_moyenne = pygame.font.Font(
            None,
            32
        )

        self.font_normal = pygame.font.Font(
            None,
            24
        )

        self.font_petit = pygame.font.Font(
            None,
            18
        )

        self.state = GameState.MENU

        self.personnage = None

        self.ennemis = pygame.sprite.Group()

        self.items = []

        self.spawn_counter = 0

        self.spawn_interval = 90

        self.combat_log = []

        self.max_combat_log = 7

        self.stats_sauvegardes = []

        self.charger_stats()

        self.running = True

        self.message_niveau = ""

        self.message_timer = 0

    # ========================================================
    # SAUVEGARDE
    # ========================================================

    def charger_stats(self):

        try:

            if os.path.exists("stats.json"):

                with open(
                    "stats.json",
                    "r",
                    encoding="utf-8"
                ) as fichier:

                    self.stats_sauvegardes = json.load(
                        fichier
                    )

        except Exception as erreur:

            print(
                "Erreur chargement:",
                erreur
            )

            self.stats_sauvegardes = []

    # --------------------------------------------------------

    def sauvegarder_stats(self):

        if self.personnage is None:
            return

        nouvelle_stat = {

            "nom":
                self.personnage.nom,

            "classe":
                self.personnage.classe,

            "niveau":
                self.personnage.stats.level,

            "experience":
                self.personnage.stats.experience,

            "or":
                self.personnage.stats.gold
        }

        self.stats_sauvegardes.append(
            nouvelle_stat
        )

        # Garde uniquement les 10 derniers
        self.stats_sauvegardes = (
            self.stats_sauvegardes[-10:]
        )

        try:

            with open(
                "stats.json",
                "w",
                encoding="utf-8"
            ) as fichier:

                json.dump(
                    self.stats_sauvegardes,
                    fichier,
                    ensure_ascii=False,
                    indent=4
                )

        except Exception as erreur:

            print(
                "Erreur sauvegarde:",
                erreur
            )

    # ========================================================
    # JOURNAL
    # ========================================================

    def ajouter_log(self, message):

        self.combat_log.insert(
            0,
            message
        )

        if len(self.combat_log) > self.max_combat_log:

            self.combat_log.pop()

    # ========================================================
    # MENU
    # ========================================================

    def menu_principal(self, events):

        self.screen.fill(BLACK)

        # Titre
        titre = self.font_grande.render(
            "RPG - AVENTURE EPIQUE",
            True,
            YELLOW
        )

        self.screen.blit(
            titre,
            (
                SCREEN_WIDTH // 2 -
                titre.get_width() // 2,
                80
            )
        )

        sous_titre = self.font_normal.render(
            "Choisissez votre classe",
            True,
            WHITE
        )

        self.screen.blit(
            sous_titre,
            (
                SCREEN_WIDTH // 2 -
                sous_titre.get_width() // 2,
                160
            )
        )

        # Guerrier
        guerrier = self.font_normal.render(
            "1 - GUERRIER",
            True,
            BLUE
        )

        self.screen.blit(
            guerrier,
            (200, 250)
        )

        texte = self.font_petit.render(
            "120 HP | ATK 18 | DEF 12",
            True,
            WHITE
        )

        self.screen.blit(
            texte,
            (200, 285)
        )

        # Magicien
        magicien = self.font_normal.render(
            "2 - MAGICIEN",
            True,
            PURPLE
        )

        self.screen.blit(
            magicien,
            (500, 250)
        )

        texte = self.font_petit.render(
            "70 HP | ATK 25 | DEF 5",
            True,
            WHITE
        )

        self.screen.blit(
            texte,
            (500, 285)
        )

        # Archer
        archer = self.font_normal.render(
            "3 - ARCHER",
            True,
            ORANGE
        )

        self.screen.blit(
            archer,
            (800, 250)
        )

        texte = self.font_petit.render(
            "90 HP | ATK 21 | DEF 8",
            True,
            WHITE
        )

        self.screen.blit(
            texte,
            (800, 285)
        )

        # Instructions
        instruction = self.font_normal.render(
            "Appuyez sur 1, 2 ou 3",
            True,
            YELLOW
        )

        self.screen.blit(
            instruction,
            (
                SCREEN_WIDTH // 2 -
                instruction.get_width() // 2,
                400
            )
        )

        # Records
        if self.stats_sauvegardes:

            titre_records = self.font_normal.render(
                "Dernières parties",
                True,
                LIGHT_GRAY
            )

            self.screen.blit(
                titre_records,
                (50, 520)
            )

            y = 560

            for stat in self.stats_sauvegardes[-5:]:

                texte = (
                    f"{stat['nom']} - "
                    f"{stat['classe']} - "
                    f"Niveau {stat['niveau']}"
                )

                surface = self.font_petit.render(
                    texte,
                    True,
                    WHITE
                )

                self.screen.blit(
                    surface,
                    (50, y)
                )

                y += 25

        # Événements
        for event in events:

            if event.type == pygame.QUIT:

                return False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_1:

                    self.demarrer_jeu(
                        "Guerrier"
                    )

                    self.state = (
                        GameState.PLAYING
                    )

                elif event.key == pygame.K_2:

                    self.demarrer_jeu(
                        "Magicien"
                    )

                    self.state = (
                        GameState.PLAYING
                    )

                elif event.key == pygame.K_3:

                    self.demarrer_jeu(
                        "Archer"
                    )

                    self.state = (
                        GameState.PLAYING
                    )

        return True

    # ========================================================
    # DÉMARRER LE JEU
    # ========================================================

    def demarrer_jeu(self, classe):

        nom = "Heros_" + classe

        self.personnage = Personnage(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            nom,
            classe
        )

        self.ennemis.empty()

        self.items.clear()

        self.combat_log.clear()

        self.spawn_counter = 0

        self.spawn_interval = 90

        self.message_niveau = ""

        self.message_timer = 0

        # Premier ennemi
        self.creer_ennemi()

    # ========================================================
    # CREATION ENNEMIS
    # ========================================================

    def creer_ennemi(self):

        if self.personnage is None:
            return

        types = [
            "Gobelin",
            "Orc"
        ]

        if self.personnage.stats.level >= 5:

            types.append(
                "Dragon"
            )

        enemy_type = random.choice(
            types
        )

        # Évite de faire apparaître
        # l'ennemi directement sur le joueur

        while True:

            x = random.randint(
                50,
                SCREEN_WIDTH - 80
            )

            y = random.randint(
                100,
                SCREEN_HEIGHT - 80
            )

            distance_x = (
                x -
                self.personnage.x
            )

            distance_y = (
                y -
                self.personnage.y
            )

            distance = (
                distance_x ** 2 +
                distance_y ** 2
            )

            if distance > 150 ** 2:
                break

        ennemi = Ennemi(
            x,
            y,
            enemy_type
        )

        self.ennemis.add(
            ennemi
        )

    # ========================================================
    # GENERATION ENNEMIS
    # ========================================================

    def generer_ennemis(self):

        if self.personnage is None:
            return

        self.spawn_counter += 1

        niveau = (
            self.personnage.stats.level
        )

        interval = max(
            35,
            self.spawn_interval -
            niveau * 5
        )

        if (
            self.spawn_counter >= interval
            and len(self.ennemis) < 6
        ):

            self.creer_ennemi()

            self.spawn_counter = 0

    # ========================================================
    # COMBATS
    # ========================================================

    def gerer_combats(self):

        if self.personnage is None:
            return

        for ennemi in list(self.ennemis):

            if self.personnage.rect.colliderect(
                ennemi.rect
            ):

                # Attaque du joueur
                joueur_degats = random.randint(
                    max(
                        1,
                        self.personnage.stats.attack - 5
                    ),
                    self.personnage.stats.attack + 5
                )

                ennemi_damage = (
                    ennemi.take_damage(
                        joueur_degats
                    )
                )

                self.ajouter_log(
                    f"Vous infligez "
                    f"{ennemi_damage} dégâts "
                    f"au {ennemi.enemy_type}."
                )

                # Si l'ennemi est mort
                if ennemi.hp <= 0:

                    xp = (
                        ennemi.exp_reward
                    )

                    or_gagne = (
                        ennemi.gold_reward
                    )

                    ancien_niveau = (
                        self.personnage.stats.level
                    )

                    self.personnage.gain_experience(
                        xp
                    )

                    self.personnage.stats.gold += (
                        or_gagne
                    )

                    self.ajouter_log(
                        f"{ennemi.enemy_type} vaincu ! "
                        f"+{xp} XP "
                        f"+{or_gagne} or."
                    )

                    # Niveau supérieur
                    if (
                        self.personnage.stats.level
                        > ancien_niveau
                    ):

                        self.message_niveau = (
                            "NIVEAU SUPERIEUR !"
                        )

                        self.message_timer = 120

                        self.ajouter_log(
                            "Vous avez gagné un niveau !"
                        )

                    # Drop
                    if random.random() < 0.50:

                        type_item = random.choice(
                            [
                                "potion",
                                "arme"
                            ]
                        )

                        if type_item == "potion":

                            item = Item(
                                "Potion de soin",
                                "potion",
                                30,
                                ennemi.x,
                                ennemi.y
                            )

                        else:

                            item = Item(
                                "Épée",
                                "arme",
                                5,
                                ennemi.x,
                                ennemi.y
                            )

                        self.items.append(
                            item
                        )

                        self.ajouter_log(
                            "Un objet est apparu !"
                        )

                    ennemi.kill()

                else:

                    # L'ennemi contre-attaque
                    if ennemi.can_attack():

                        ennemi_degats = random.randint(
                            max(
                                1,
                                ennemi.attack - 3
                            ),
                            ennemi.attack + 3
                        )

                        joueur_damage = (
                            self.personnage.take_damage(
                                ennemi_degats
                            )
                        )

                        self.ajouter_log(
                            f"{ennemi.enemy_type} "
                            f"vous inflige "
                            f"{joueur_damage} dégâts."
                        )

                        ennemi.reset_attack()

    # ========================================================
    # ITEMS
    # ========================================================

    def gerer_items(self):

        if self.personnage is None:
            return

        items_supprimer = []

        for item in self.items:

            if self.personnage.rect.colliderect(
                item.rect
            ):

                if item.type == "potion":

                    soin = self.personnage.heal(
                        item.valeur
                    )

                    self.ajouter_log(
                        f"Potion : +{soin} HP."
                    )

                elif item.type == "arme":

                    self.personnage.stats.attack += (
                        item.valeur
                    )

                    self.ajouter_log(
                        f"Épée : +{item.valeur} ATK."
                    )

                self.personnage.add_item(
                    item
                )

                items_supprimer.append(
                    item
                )

        for item in items_supprimer:

            if item in self.items:

                self.items.remove(
                    item
                )

    # ========================================================
    # HUD
    # ========================================================

    def afficher_hud(self):

        if self.personnage is None:
            return

        # Fond du HUD
        pygame.draw.rect(
            self.screen,
            DARK_GRAY,
            (0, 0, SCREEN_WIDTH, 75)
        )

        pygame.draw.line(
            self.screen,
            LIGHT_GRAY,
            (0, 75),
            (SCREEN_WIDTH, 75),
            2
        )

        stats = self.personnage.stats

        ligne1 = (
            f"{self.personnage.nom} | "
            f"{self.personnage.classe}"
        )

        ligne2 = (
            f"Niveau {stats.level} | "
            f"XP {stats.experience}/"
            f"{stats.level * 100}"
        )

        ligne3 = (
            f"HP {stats.hp}/{stats.max_hp} | "
            f"ATK {stats.attack} | "
            f"DEF {stats.defense}"
        )

        ligne4 = (
            f"Or : {stats.gold} | "
            f"Ennemis : {len(self.ennemis)}"
        )

        textes = [
            ligne1,
            ligne2,
            ligne3,
            ligne4
        ]

        x_positions = [
            10,
            300,
            600,
            900
        ]

        for texte, x in zip(
            textes,
            x_positions
        ):

            surface = self.font_petit.render(
                texte,
                True,
                WHITE
            )

            self.screen.blit(
                surface,
                (x, 25)
            )

    # ========================================================
    # JOURNAL DE COMBAT
    # ========================================================

    def afficher_combat_log(self):

        x = SCREEN_WIDTH - 370
        y = 95

        width = 350
        height = 180

        # Fond
        pygame.draw.rect(
            self.screen,
            (35, 35, 35),
            (
                x,
                y,
                width,
                height
            )
        )

        pygame.draw.rect(
            self.screen,
            LIGHT_GRAY,
            (
                x,
                y,
                width,
                height
            ),
            2
        )

        titre = self.font_petit.render(
            "JOURNAL DE COMBAT",
            True,
            YELLOW
        )

        self.screen.blit(
            titre,
            (
                x + 10,
                y + 10
            )
        )

        position_y = y + 35

        for message in self.combat_log:

            # Coupe les messages trop longs
            if len(message) > 42:
                message = message[:39] + "..."

            texte = self.font_petit.render(
                message,
                True,
                WHITE
            )

            self.screen.blit(
                texte,
                (
                    x + 10,
                    position_y
                )
            )

            position_y += 20

    # ========================================================
    # ÉCRAN DE JEU
    # ========================================================

    def afficher_jeu(self):

        self.screen.fill(
            (15, 20, 25)
        )

        # Sol
        pygame.draw.rect(
            self.screen,
            (25, 35, 30),
            (
                0,
                75,
                SCREEN_WIDTH,
                SCREEN_HEIGHT - 75
            )
        )

        # Petits éléments du décor
        for x in range(
            0,
            SCREEN_WIDTH,
            80
        ):

            pygame.draw.line(
                self.screen,
                (30, 45, 35),
                (
                    x,
                    75
                ),
                (
                    x,
                    SCREEN_HEIGHT
                )
            )

        for y in range(
            80,
            SCREEN_HEIGHT,
            80
        ):

            pygame.draw.line(
                self.screen,
                (30, 45, 35),
                (
                    0,
                    y
                ),
                (
                    SCREEN_WIDTH,
                    y
                )
            )

        # Objets
        for item in self.items:

            item.draw(
                self.screen
            )

        # Ennemis
        for ennemi in self.ennemis:

            ennemi.draw(
                self.screen
            )

        # Joueur
        if self.personnage:

            self.personnage.draw(
                self.screen
            )

        # HUD
        self.afficher_hud()

        # Journal
        self.afficher_combat_log()

        # Instructions
        instructions = self.font_petit.render(
            "ZQSD / Fleches : déplacer | "
            "I : inventaire | "
            "ESC : quitter",
            True,
            LIGHT_GRAY
        )

        self.screen.blit(
            instructions,
            (
                10,
                SCREEN_HEIGHT - 30
            )
        )

        # Message de niveau
        if self.message_timer > 0:

            message = self.font_grande.render(
                self.message_niveau,
                True,
                YELLOW
            )

            self.screen.blit(
                message,
                (
                    SCREEN_WIDTH // 2 -
                    message.get_width() // 2,
                    120
                )
            )

            self.message_timer -= 1

    # ========================================================
    # INVENTAIRE
    # ========================================================

    def afficher_inventaire(
        self,
        events
    ):

        self.screen.fill(
            BLACK
        )

        titre = self.font_grande.render(
            "INVENTAIRE",
            True,
            YELLOW
        )

        self.screen.blit(
            titre,
            (
                SCREEN_WIDTH // 2 -
                titre.get_width() // 2,
                50
            )
        )

        if self.personnage is None:
            return False

        if not self.personnage.inventory:

            texte = self.font_normal.render(
                "Votre inventaire est vide.",
                True,
                WHITE
            )

            self.screen.blit(
                texte,
                (
                    SCREEN_WIDTH // 2 -
                    texte.get_width() // 2,
                    200
                )
            )

        else:

            y = 150

            for i, item in enumerate(
                self.personnage.inventory
            ):

                texte = (
                    f"{i + 1}. "
                    f"{item.nom} | "
                    f"Type : {item.type} | "
                    f"Valeur : {item.valeur}"
                )

                surface = self.font_normal.render(
                    texte,
                    True,
                    WHITE
                )

                self.screen.blit(
                    surface,
                    (100, y)
                )

                y += 45

        instructions = self.font_petit.render(
            "Appuyez sur I pour revenir au jeu",
            True,
            LIGHT_GRAY
        )

        self.screen.blit(
            instructions,
            (
                SCREEN_WIDTH // 2 -
                instructions.get_width() // 2,
                SCREEN_HEIGHT - 60
            )
        )

        for event in events:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_i:

                    return False

                if event.key == pygame.K_ESCAPE:

                    return False

        return True

    #
    
    ========================================================
    # GAME OVER
    # ========================================================

    def afficher_game_over(
        self,
        events
    ):

        self.screen.fill(
            BLACK
        )

        titre = self.font_grande.render(
            "GAME OVER",
            True,
            RED
        )

        self.screen.blit(
            titre,
            (
                SCREEN_WIDTH // 2 -
                titre.get_width() // 2,
                120
            )
        )

        if self.personnage:

            stats = [

                f"Nom : {self.personnage.nom}",

                f"Classe : "
                f"{self.personnage.classe}",

                f"Niveau atteint : "
                f"{self.personnage.stats.level}",

                f"XP : "
                f"{self.personnage.stats.experience}",

                f"Or collecté : "
                f"{self.personnage.stats.gold}"

            ]

            y = 250

            for texte in stats:

                surface = self.font_normal.render(
                    texte,
                    True,
                    WHITE
                )

                self.screen.blit(
                    surface,
                    (
                        SCREEN_WIDTH // 2 -
                        surface.get_width() // 2,
                        y
                    )
                )

                y += 45

        instruction = self.font_normal.render(
            "ESPACE : retourner au menu",
            True,
            YELLOW
        )

        self.screen.blit(
            instruction,
            (
                SCREEN_WIDTH // 2 -
                instruction.get_width() // 2,
                550
            )
        )

        for event in events:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:

                    self.sauvegarder_stats()

                    self.state = (
                        GameState.MENU
                    )

                    self.personnage = None

                    self.ennemis.empty()

                    self.items.clear()

        return True

    # ========================================================
    # MISE À JOUR DU JEU
    # ========================================================

    def mettre_a_jour(self):

        if self.personnage is None:
            return

        keys = pygame.key.get_pressed()

        self.personnage.update(
            keys
        )

        # Mise à jour des ennemis
        self.ennemis.update()

        # Création des ennemis
        self.generer_ennemis()

        # Combats
        self.gerer_combats()

        # Items
        self.gerer_items()

        # Mort
        if self.personnage.stats.hp <= 0:

            self.state = (
                GameState.GAME_OVER
            )

    # ========================================================
    # BOUCLE PRINCIPALE
    # ========================================================

    def boucle_principale(self):

        while self.running:

            events = pygame.event.get()

            # ------------------------------------------------
            # ÉVÉNEMENTS GÉNÉRAUX
            # ------------------------------------------------

            for event in events:

                if event.type == pygame.QUIT:

                    self.running = False

                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):

                    if self.state == GameState.PLAYING:

                        self.running = False

            # ------------------------------------------------
            # MENU
            # ------------------------------------------------

            if self.state == GameState.MENU:

                if not self.menu_principal(
                    events
                ):

                    self.running = False

            # ------------------------------------------------
            # JEU
            # ------------------------------------------------

            elif self.state == GameState.PLAYING:

                # I = inventaire
                for event in events:

                    if event.type == pygame.KEYDOWN:

                        if event.key == pygame.K_i:

                            self.state = (
                                GameState.INVENTORY
                            )

                if self.state == GameState.PLAYING:

                    self.mettre_a_jour()

                    self.afficher_jeu()

            # ------------------------------------------------
            # INVENTAIRE
            # ------------------------------------------------

            elif self.state == GameState.INVENTORY:

                self.afficher_inventaire(
                    events
                )

                # Vérification de I
                for event in events:

                    if event.type == pygame.KEYDOWN:

                        if event.key == pygame.K_i:

                            self.state = (
                                GameState.PLAYING
                            )

                        elif event.key == pygame.K_ESCAPE:

                            self.state = (
                                GameState.PLAYING
                            )

            # ------------------------------------------------
            # GAME OVER
            # ------------------------------------------------

            elif self.state == GameState.GAME_OVER:

                self.afficher_game_over(
                    events
                )

            # ------------------------------------------------
            # AFFICHAGE
            # ------------------------------------------------

            pygame.display.flip()

            CLOCK.tick(FPS)

        pygame.quit()

        sys.exit()


# ============================================================
# LANCEMENT DU PROGRAMME
# ============================================================

def main():

    try:

        jeu = Jeu()

        jeu.boucle_principale()

    except Exception as erreur:

        # Affiche l'erreur dans la console Pydroid
        print(
            "\n=============================="
        )

        print(
            "ERREUR DU JEU :"
        )

        print(
            erreur
        )

        print(
            "=============================="
        )

        pygame.quit()

        raise


if __name__ == "__main__":

    main()