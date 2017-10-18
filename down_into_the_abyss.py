# coding=utf-8
import bs
import bsSpaz
import bsPowerup
import math
import random
import bsUtils
from bsMap import Map, registerMap


class AbyssMap(Map):
    import alwaysLandLevelDefs as defs
    # Add the y-dimension space for players
    defs.boxes['levelBounds'] = (-0.8748348681, 9.212941713, -9.729538885) \
                                + (0.0, 0.0, 0.0) \
                                + (36.09666006, 26.19950145, 20.89541168)
    name = 'Abyss Unhappy'
    playTypes = ['abyss']

    @classmethod
    def getPreviewTextureName(cls):
        return 'alwaysLandPreview'

    @classmethod
    def onPreload(cls):
        data = {}
        data['model'] = bs.getModel('alwaysLandLevel')
        data['bottomModel'] = bs.getModel('alwaysLandLevelBottom')
        data['bgModel'] = bs.getModel('alwaysLandBG')
        data['collideModel'] = bs.getCollideModel('alwaysLandLevelCollide')
        data['tex'] = bs.getTexture('alwaysLandLevelColor')
        data['bgTex'] = bs.getTexture('alwaysLandBGColor')
        data['vrFillMoundModel'] = bs.getModel('alwaysLandVRFillMound')
        data['vrFillMoundTex'] = bs.getTexture('vrFillMound')
        return data

    @classmethod
    def getMusicType(cls):
        return 'Flying'

    def __init__(self):
        Map.__init__(self, vrOverlayCenterOffset=(0, -3.7, 2.5))

        self.foo = bs.newNode('terrain',
                              attrs={'model': self.preloadData['bgModel'],
                                     'lighting': False,
                                     'background': True,
                                     'colorTexture': self.preloadData['bgTex']})
        bs.newNode('terrain',
                   attrs={'model': self.preloadData['vrFillMoundModel'],
                          'lighting': False,
                          'vrOnly': True,
                          'color': (0.2, 0.25, 0.2),
                          'background': True,
                          'colorTexture': self.preloadData['vrFillMoundTex']})
        g = bs.getSharedObject('globals')
        g.happyThoughtsMode = True
        g.shadowOffset = (0.0, 8.0, 5.0)
        g.tint = (1.3, 1.23, 1.0)
        g.ambientColor = (1.3, 1.23, 1.0)
        g.vignetteOuter = (0.64, 0.59, 0.69)
        g.vignetteInner = (0.95, 0.95, 0.93)
        g.vrNearClip = 1.0
        self.isFlying = True


registerMap(AbyssMap)


class SpazTouchFoothold(object):
    pass


class BombToDieMessage(object):
    pass


class Foothold(bs.Actor):
    def __init__(self, position, power='random', size=6, breakable=True, moving=False):
        bs.Actor.__init__(self)
        factory = self.getFactory()

        fmodel = factory.model
        fmodels = factory.modelSimple
        self.died = False
        self.breakable = breakable
        self.moving = moving  # move right and left
        self.lrSig = 1  # left or right signal
        self.lrSpeedPlus = random.uniform(1 / 2.0, 1 / 0.7)
        self._npcBots = bs.BotSet()

        tex = {
            'punch': factory.texPunch,
            'sticky': factory.texStickyBombs,
            'ice': factory.texIceBombs,
            'impact': factory.texImpactBombs,
            'health': factory.texHealth,
            'curse': factory.texCurse,
            'shield': factory.texShield,
            'landmine': factory.texLandMines,
            'tnt': factory.texTNT,
        }.get(power, factory.texTNT)
        if power == 'random':
            random.seed()
            tex = random.choice(factory.randTex)
        self.tex = tex
        self.powerupType = {
            factory.texPunch: 'punch',
            factory.texBomb: 'tripleBombs',
            factory.texIceBombs: 'iceBombs',
            factory.texImpactBombs: 'impactBombs',
            factory.texLandMines: 'landMines',
            factory.texStickyBombs: 'stickyBombs',
            factory.texShield: 'shield',
            factory.texHealth: 'health',
            factory.texCurse: 'curse',
            factory.texTNT: 'tnt'
        }.get(self.tex, '')

        self._spawnPos = (position[0], position[1], position[2])

        self.node = bs.newNode('prop',
                               delegate=self,
                               attrs={'body': 'landMine',
                                      'position': self._spawnPos,
                                      'model': fmodel,
                                      'lightModel': fmodels,
                                      'shadowSize': 0.5,
                                      'velocity': (0, 0, 0),
                                      'density': 90000000000,
                                      'sticky': False,
                                      'bodyScale': size,
                                      'modelScale': size,
                                      'colorTexture': tex,
                                      'reflection': 'powerup',
                                      'isAreaOfInterest': True,
                                      'gravityScale': 0.0,
                                      'reflectionScale': [0],
                                      'materials': (
                                          factory.footholdMaterial,
                                          bs.getSharedObject('objectMaterial'),
                                          bs.getSharedObject('footingMaterial')
                                      )})
        self.touchedSpazs = set()

        self.keepVel()

    def keepVel(self):
        if self.node.exists() and not self.died:
            speed = self.getActivity().cur_speed
            if self.moving:
                if abs(self.node.position[0]) > 10:
                    self.lrSig *= -1
                self.node.velocity = (self.lrSig * speed * self.lrSpeedPlus, speed, 0)
                bs.gameTimer(100, bs.WeakCall(self.keepVel))
            else:
                self.node.velocity = (0, speed, 0)
                # self.node.extraAcceleration = (0, self.speed, 0)
                bs.gameTimer(100, bs.WeakCall(self.keepVel))

    def tntExplode(self):
        pos = self.node.position
        bs.Blast(position=pos, blastRadius=6.0,
                 blastType='tnt',
                 sourcePlayer=None).autoRetain()

    def spawnNPC(self):
        if not self.breakable:
            return
        if self._npcBots.haveLivingBots():
            return
        if random.randint(0, 3) >= self.getActivity().npc_density:
            return
        pos = self.node.position
        pos = (pos[0], pos[1] + 1, pos[2])
        self._npcBots.spawnBot(botType=random.choice([
            bsSpaz.NinjaBotPro,
            bsSpaz.ChickBotPro
        ]), pos=pos, spawnTime=10)

    def handleMessage(self, m):
        super(self.__class__, self).handleMessage(m)

        if isinstance(m, bs.DieMessage):
            self.node.delete()
            self.died = True
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())
        elif isinstance(m, BombToDieMessage):
            if self.powerupType == 'tnt':
                self.tntExplode()
            self.handleMessage(bs.DieMessage())
        elif isinstance(m, bs.HitMessage):
            isPunch = (m.srcNode.exists() and m.srcNode.getNodeType() == 'spaz')
            if not isPunch:
                if self.breakable:
                    self.handleMessage(BombToDieMessage())
        elif isinstance(m, SpazTouchFoothold):
            node = bs.getCollisionInfo("opposingNode")
            if node is not None and node.exists():
                try:
                    spaz = node.getDelegate()
                    if not isinstance(spaz, AbyssPlayerSpaz):
                        return
                    if spaz in self.touchedSpazs:
                        return
                    self.touchedSpazs.add(spaz)
                    self.spawnNPC()
                    spaz.fix_2D_position()
                    if self.powerupType not in ['', 'tnt']:
                        node.handleMessage(bsPowerup.PowerupMessage(self.powerupType))
                except Exception, e:
                    print e
                    pass

    @classmethod
    def getFactory(cls):
        """
        Returns a shared factory object, creating it if necessary.
        """
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try:
            return activity._sharedFootholdFactory
        except Exception:
            f = activity._sharedFootholdFactory = FootholdFactory()
            return f


class FootholdFactory(object):
    def __init__(self):
        self.model = bs.getModel("landMine")
        self.modelSimple = bs.getModel("powerupSimple")

        self.texBomb = bs.getTexture("powerupBomb")
        self.texPunch = bs.getTexture("powerupPunch")
        self.texIceBombs = bs.getTexture("powerupIceBombs")
        self.texStickyBombs = bs.getTexture("powerupStickyBombs")
        self.texShield = bs.getTexture("powerupShield")
        self.texImpactBombs = bs.getTexture("powerupImpactBombs")
        self.texHealth = bs.getTexture("powerupHealth")
        self.texLandMines = bs.getTexture("powerupLandMines")
        self.texCurse = bs.getTexture("powerupCurse")
        self.texTNT = bs.getTexture("tnt")

        self.powerupDistribution = {
            self.texBomb: 3,
            self.texIceBombs: 2,
            self.texPunch: 3,
            self.texImpactBombs: 3,
            self.texLandMines: 3,
            self.texStickyBombs: 4,
            self.texShield: 4,
            self.texHealth: 3,
            self.texCurse: 1,
            self.texTNT: 2
        }

        self.randTex = []

        for keyTex in self.powerupDistribution:
            for i in range(self.powerupDistribution[keyTex]):
                self.randTex.append(keyTex)

        self.footholdMaterial = bs.Material()
        self.impactSound = bs.getSound('impactMedium')

        self.footholdMaterial.addActions(conditions=(
            ('theyDontHaveMaterial', bs.getSharedObject('playerMaterial')), 'and',
            ('theyHaveMaterial', bs.getSharedObject('objectMaterial')), 'or',
            ('theyHaveMaterial', bs.getSharedObject('footingMaterial'))),
            actions=(
                ('modifyNodeCollision', 'collide', True),
            ))

        self.footholdMaterial.addActions(
            conditions=('theyHaveMaterial', bs.getSharedObject('playerMaterial')),
            actions=(('modifyPartCollision', 'physical', True),
                     ('modifyPartCollision', 'stiffness', 0.05),
                     ('message', 'ourNode', 'atConnect', SpazTouchFoothold())))

        self.footholdMaterial.addActions(
            conditions=(
                ('theyHaveMaterial', self.footholdMaterial)
            ),
            actions=(('modifyNodeCollision', 'collide', False)))


class AbyssPlayerSpaz(bs.PlayerSpaz):
    def __init__(self, color=(1, 1, 1), highlight=(0.5, 0.5, 0.5),
                 character="Spaz", player=None, powerupsExpire=True):
        bs.PlayerSpaz.__init__(
            self,
            color=color,
            highlight=highlight,
            character=character,
            player=player,
            powerupsExpire=powerupsExpire
        )
        self.node.fly = False
        self.node.hockey = True
        self.hitPointsMax = self.hitPoints = 1500  # more HP to handle drop
        bs.gameTimer(self.getActivity().peace_time, bs.WeakCall(self.safeConnectControlsToPlayer))

    def safeConnectControlsToPlayer(self):
        try:
            self.connectControlsToPlayer()
        except:
            pass

    def onMoveUpDown(self, value):
        if not self.node.exists(): return
        if self.node.run > 0.1:
            self.node.moveUpDown = value
        else:
            self.node.moveUpDown = value / 3.

    def onMoveLeftRight(self, value):
        if not self.node.exists(): return
        if self.node.run > 0.1:
            self.node.moveLeftRight = value
        else:
            self.node.moveLeftRight = value / 1.5

    def fix_2D_position(self):
        self.node.fly = True
        bs.gameTimer(20, bs.WeakCall(self.disable_fly))

    def disable_fly(self):
        if self.node.exists():
            self.node.fly = False

    def curse(self):
        if not self._cursed:
            factory = self.getFactory()
            self._cursed = True
            for attr in ['materials', 'rollerMaterials']:
                materials = getattr(self.node, attr)
                if not factory.curseMaterial in materials:
                    setattr(self.node, attr, materials + (factory.curseMaterial,))

            # -1 specifies no time limit
            if self.curseTime == -1:
                self.node.curseDeathTime = -1
            else:
                self.node.curseDeathTime = bs.getGameTime() + 15000
                bs.gameTimer(15000, bs.WeakCall(self.curseExplode))

    def handleMessage(self, m):
        dontUp = False

        if isinstance(m, bsSpaz._PickupMessage):
            dontUp = True
            opposingNode, opposingBody = bs.getCollisionInfo('opposingNode', 'opposingBody')

            if opposingNode is None or not opposingNode.exists(): return True
            opposingDelegate = opposingNode.getDelegate()
            # Don't pick up the foothold
            if isinstance(opposingDelegate, Foothold):
                return True

            # dont allow picking up of invincible dudes
            try:
                if opposingNode.invincible == True: return True
            except Exception:
                pass

            # if we're grabbing the pelvis of a non-shattered spaz, we wanna grab the torso instead
            if opposingNode.getNodeType() == 'spaz' and not opposingNode.shattered and opposingBody == 4:
                opposingBody = 1

            # special case - if we're holding a flag, dont replace it
            # ( hmm - should make this customizable or more low level )
            held = self.node.holdNode
            if held is not None and held.exists() and held.getNodeType() == 'flag':
                return True

            self.node.holdBody = opposingBody  # needs to be set before holdNode
            self.node.holdNode = opposingNode

        if not dontUp:
            bs.PlayerSpaz.handleMessage(self, m)


def bsGetAPIVersion():
    return 4


def bsGetGames():
    return [AbyssGame]


class AbyssLangChinese(object):
    name = '无尽深渊'
    description = '在无穷尽的坠落中存活更长时间'
    help = ''
    author = '作者: Deva'
    github = 'GitHub: spdv123'
    blog = '博客: superdeva.info'

    peaceTime = '和平时间'
    npcDensity = 'NPC密度'

    hint_use_punch = u'现在可以使用拳头痛扁你的敌人了'


class AbyssLangEnglish(object):
    name = 'Down Into The Abyss'
    description = 'Survive as long as you can'
    help = 'The map is 3D, be careful!'
    author = 'Author: Deva'
    github = 'GitHub: spdv123'
    blog = 'Blog: superdeva.info'

    peaceTime = 'Peace Time'
    npcDensity = 'NPC Density'

    hint_use_punch = 'You can punch your enemies now!'


AbyssLang = AbyssLangEnglish
if bs.getLanguage() == 'Chinese':
    AbyssLang = AbyssLangChinese


def bsGetLevels():
    return [bs.Level(AbyssLang.name, displayName='${GAME}', gameType=AbyssGame,
                     settings={"Epic Mode": True,
                               AbyssLang.peaceTime: 0,
                               AbyssLang.npcDensity: 3}, previewTexName='alwaysLandPreview')]


class AbyssGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return AbyssLang.name

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName': 'Survived',
                'scoreType': 'milliseconds',
                'scoreVersion': 'B'}

    @classmethod
    def getDescription(cls, sessionType):
        return AbyssLang.description

    def getInstanceDescription(self):
        return AbyssLang.description

    def getInstanceScoreBoardDescription(self):
        return self.getInstanceDescription() + '\n' + AbyssLang.help

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return [u'Abyss Unhappy']
        # return bs.getMapsSupportingPlayType("melee")

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False}),
                (AbyssLang.peaceTime, {
                    'choices': [
                        ('None', 1),
                        ('Shorter', 2500),
                        ('Short', 5000),
                        ('Normal', 10000),
                        ('Long', 15000),
                        ('Longer', 20000)
                    ],
                    'default': 10000}),
                (AbyssLang.npcDensity, {
                    'choices': [
                        ('0%', 0),
                        ('25%', 1),
                        ('50%', 2),
                        ('75%', 3),
                        ('100%', 4)
                    ],
                    'default': 2})]

    # we support teams, free-for-all, and co-op sessions
    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if (issubclass(sessionType, bs.TeamsSession)
                        or issubclass(sessionType, bs.FreeForAllSession)
                        or issubclass(sessionType, bs.CoopSession)) else False

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)

        if self.settings['Epic Mode']: self._isSlowMotion = True

        # print messages when players die (since its meaningful in this game)
        self.announcePlayerDeaths = True
        self.fix_y = -5.614479365
        self.start_z = 0
        self.init_position = (0, self.start_z, self.fix_y)
        self.team_init_positions = [(-5, self.start_z, self.fix_y),
                                    (5, self.start_z, self.fix_y)]
        self.cur_speed = 2.5
        # TODO: The variable below should be set in settings
        self.peace_time = self.settings[AbyssLang.peaceTime]
        self.npc_density = self.settings[AbyssLang.npcDensity]

        self._lastPlayerDeathTime = None

        self._gameCredit = bs.NodeActor(bs.newNode('text',
                                                   attrs={'vAttach': 'bottom',
                                                          'hAlign': 'center',
                                                          'vrDepth': 0,
                                                          'color': (0, 0, 0.8),
                                                          'shadow': 1.0 if True else 0.5,
                                                          'flatness': 1.0 if True else 0.5,
                                                          'position': (0, 0),
                                                          'scale': 0.8,
                                                          'text': ' | '.join(
                                                              [AbyssLang.author,
                                                               AbyssLang.github,
                                                               AbyssLang.blog]
                                                          ),
                                                          }))

    # called when our game is transitioning in but not ready to start..
    # ..we can go ahead and set our music and whatnot
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')

    def onPlayerJoin(self, player):
        if self.hasBegun():
            player.gameData['notIn'] = True
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText', subs=[('${PLAYER}', player.getName(full=True))]),
                             color=(0, 1, 0))
            return
        self.spawnPlayer(player)

    # called when our game actually starts
    def onBegin(self):

        bs.TeamGameActivity.onBegin(self)

        self._timer = bs.OnScreenTimer()
        self._timer.start()

        self.level_cnt = 1

        if self.teamsOrFFA() == 'teams':
            ip0 = self.team_init_positions[0]
            ip1 = self.team_init_positions[1]
            Foothold((ip0[0], ip0[1] - 2, ip0[2]), power='shield', breakable=False).autoRetain()
            Foothold((ip1[0], ip1[1] - 2, ip1[2]), power='shield', breakable=False).autoRetain()
        else:
            ip = self.init_position
            Foothold((ip[0], ip[1] - 2, ip[2]), power='shield', breakable=False).autoRetain()

        bs.gameTimer(int(5000 / self.cur_speed), bs.WeakCall(self.add_foothold), repeat=True)

        bs.gameTimer(1000, self._checkEndGame, repeat=True)  # Repeat check game end
        bs.gameTimer(self.peace_time + 100, bs.WeakCall(self.tip_hint, AbyssLang.hint_use_punch))
        bs.gameTimer(6000, bs.WeakCall(self.faster_speed), repeat=True)

    def tip_hint(self, msg):
        bs.screenMessage(msg, color=(0.2, 0.2, 1))

    def faster_speed(self):
        self.cur_speed *= 1.15

    def add_foothold(self):
        ip = self.init_position
        ip_1 = (ip[0] - 7, ip[1], ip[2])
        ip_2 = (ip[0] + 7, ip[1], ip[2])
        ru = random.uniform
        self.level_cnt += 1
        if self.level_cnt % 3:
            Foothold((ip_1[0] + ru(-5, 5), ip[1] - 2, ip[2] + ru(-0.0, 0.0))).autoRetain()
            Foothold((ip_2[0] + ru(-5, 5), ip[1] - 2, ip[2] + ru(-0.0, 0.0))).autoRetain()
        else:
            Foothold((ip[0] + ru(-8, 8), ip[1] - 2, ip[2]), moving=True).autoRetain()

    def teamsOrFFA(self):
        if isinstance(self.getSession(), bs.TeamsSession):
            return 'teams'
        return 'ffa'

    def spawnPlayerSpaz(self, player):
        position = self.init_position
        if self.teamsOrFFA() == 'teams':
            position = self.team_init_positions[
                player.getTeam().getID() % 2
                ]

        angle = None

        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color, targetIntensity=0.75)
        spaz = AbyssPlayerSpaz(color=color,
                               highlight=highlight,
                               character=player.character,
                               player=player)
        player.setActor(spaz)

        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer(enablePunch=False,
                                     enableBomb=True,
                                     enablePickUp=False)
        self.scoreSet.playerGotNewSpaz(player, spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(bs.StandMessage(position, angle if angle is not None else random.uniform(0, 360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound, 1, position=spaz.node.position)
        light = bs.newNode('light', attrs={'color': lightColor})
        spaz.node.connectAttr('position', light, 'position')
        bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
        bs.gameTimer(500, light.delete)
        spaz.playBigDeathSound = True
        return spaz

    def spawnPlayer(self, player):
        spaz = self.spawnPlayerSpaz(player)

    # various high-level game events come through this method
    def handleMessage(self, m):

        if isinstance(m, bs.PlayerSpazDeathMessage):

            bs.TeamGameActivity.handleMessage(self, m)  # (augment standard behavior)

            deathTime = bs.getGameTime()

            # record the player's moment of death
            m.spaz.getPlayer().gameData['deathTime'] = deathTime

            # in co-op mode, end the game the instant everyone dies (more accurate looking)
            # in teams/ffa, allow a one-second fudge-factor so we can get more draws
            if isinstance(self.getSession(), bs.CoopSession):
                # teams will still show up if we check now.. check in the next cycle
                bs.pushCall(self._checkEndGame)
                self._lastPlayerDeathTime = deathTime  # also record this for a final setting of the clock..
            else:
                bs.gameTimer(1000, self._checkEndGame)

        else:
            # default handler:
            bs.TeamGameActivity.handleMessage(self, m)

    def _checkEndGame(self):
        livingTeamCount = 0
        for team in self.teams:
            for player in team.players:
                if player.isAlive():
                    livingTeamCount += 1
                    break

        # in co-op, we go till everyone is dead.. otherwise we go until one team remains
        if isinstance(self.getSession(), bs.CoopSession):
            if livingTeamCount <= 0: self.endGame()
        else:
            if livingTeamCount <= 0: self.endGame()

    def endGame(self):
        curTime = bs.getGameTime()
        for team in self.teams:
            for player in team.players:
                if 'notIn' in player.gameData:
                    player.gameData['deathTime'] = 0
                elif 'deathTime' not in player.gameData:
                    player.gameData['deathTime'] = curTime + 1
                score = (player.gameData['deathTime'] - self._timer.getStartTime()) / 1000
                if 'deathTime' not in player.gameData:
                    score += 50
                self.scoreSet.playerScored(player, score, screenMessage=False)

        # stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endTime=self._lastPlayerDeathTime)

        # ok now calc game results: set a score for each team and then tell the game to end
        results = bs.TeamGameResults()

        # remember that 'free-for-all' mode is simply a special form of 'teams' mode
        # where each player gets their own team, so we can just always deal in teams
        # and have all cases covered
        for team in self.teams:

            # set the team score to the max time survived by any player on that team
            longestLife = 0
            for player in team.players:
                longestLife = max(longestLife, (player.gameData['deathTime'] - self._timer.getStartTime()))
            results.setTeamScore(team, longestLife)

        self.end(results=results)
