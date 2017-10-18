# coding=utf-8
import bs
import bsUtils
import copy
import weakref
import random
import math


def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4


def bsGetGames():
    return [BrickWorldGame]


class changeOwnerMessage(object):
    def __init__(self):
        pass


class Brick(bs.Actor):
    def __init__(self, spaz, size=3, dieWhenOwnerDie=True, lifeTime=20000, color='yellow', breakable=True):
        bs.Actor.__init__(self)
        factory = self.getFactory()

        fmodel = factory.model
        fmodels = factory.modelSimple
        self.breakable = breakable

        tex = {
            'red': factory.texPunch,
            'green': factory.texStickyBombs,
            'blue': factory.texIceBombs,
            'silver': factory.texImpactBombs,
            'white': factory.texHealth,
            'black': factory.texCurse,
            'purple': factory.texShield,
            'yellow': factory.texTNT,
        }.get(color, factory.texTNT)
        if color == 'random':
            random.seed()
            tex = random.choice(factory.randTex)
        self.spazRef = weakref.ref(spaz)

        p1 = spaz.node.positionCenter
        p2 = spaz.node.positionForward
        direction = [p1[0] - p2[0], p2[1] - p1[1], p1[2] - p2[2]]
        direction[1] = 0.0
        brick_a = 2. / 3
        dir_2 = [2 * brick_a if direction[0] > 0 else -brick_a, 0, 2 * brick_a if direction[2] > 0 else -brick_a]
        if abs(direction[0]) > abs(direction[2]):
            dir_2[2] = 0
        else:
            dir_2[0] = 0
        position = (int(p1[0] / brick_a) * brick_a + dir_2[0], 3, int(p1[2] / brick_a) * brick_a + dir_2[2])

        self._spawnPos = (position[0], position[1], position[2])
        activity = bs.getActivity()
        self.topHeight = activity.getMap().getDefBoundBox('levelBounds')[4] - brick_a
        self._spawnPos = (p2[0], p2[1], p2[2])

        self.node = bs.newNode('prop',
                               delegate=self,
                               attrs={'body': 'crate',
                                      'position': self._spawnPos,
                                      'model': fmodel,
                                      'lightModel': fmodels,
                                      'shadowSize': 0.5,
                                      'velocity': (0, 0, 0),
                                      'density': 2000,
                                      'sticky': False,
                                      'stickToOwner': False,
                                      'owner': spaz.node,
                                      'bodyScale': size,
                                      'modelScale': size,
                                      'colorTexture': tex,
                                      'reflection': 'powerup',
                                      'damping': 1000,
                                      # 'gravityScale': 0.2,
                                      'reflectionScale': [0],
                                      'materials': (
                                          factory.brickMaterial,
                                          bs.getSharedObject('objectMaterial'),
                                          bs.getSharedObject('footingMaterial')
                                      )})
        self.transferPeople(p2, size)

        if dieWhenOwnerDie:
            bs.gameTimer(500, bs.WeakCall(self.checkDeath))
        bs.gameTimer(lifeTime, bs.WeakCall(self.handleMessage, bs.DieMessage()))
        self.died = False

    def transferPeople(self, center, size):
        players = bs.getActivity().players
        for p in players:
            try:
                spaz = p.actor
                spazPos = spaz.node.position
                if self.calcDistance(spazPos, center) < size * 0.33:
                    spaz.handleMessage(bs.StandMessage(
                        (center[0], center[1] + size * 0.35, center[2]),
                        random.uniform(0, 360)
                    ))
            except:
                pass

    @staticmethod
    def calcDistance(pos1, pos2):
        return math.sqrt(math.fsum([abs(pos1[k] - pos2[k]) for k in range(3)]))

    def checkDeath(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.isAlive():
            self.handleMessage(bs.DieMessage())
            return
        bs.gameTimer(500, bs.WeakCall(self.checkDeath))

    def changeVelToZero(self):
        try:
            self.node.velocity = (0, 0, 0)
        except:
            pass

    def handleMessage(self, m):
        super(self.__class__, self).handleMessage(m)

        if isinstance(m, bs.DieMessage):
            self.node.delete()
            self.died = True
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())
        elif isinstance(m, changeOwnerMessage):
            node, body = bs.getCollisionInfo("opposingNode", "opposingBody")
            if node is not None and node.exists():
                try:
                    spaz = node.getDelegate()
                    if spaz.getPlayer().getTeam() == self.node.owner.getDelegate().getPlayer().getTeam():
                        self.node.owner = node
                except:
                    pass
        elif isinstance(m, bs.HitMessage):
            if m.hitType == 'punch' and self.breakable:
                self.handleMessage(bs.DieMessage())

    @classmethod
    def getFactory(cls):
        """
        Returns a shared factory object, creating it if necessary.
        """
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try:
            return activity._sharedBrickFactory
        except Exception:
            f = activity._sharedBrickFactory = BrickFactory()
            return f


class BrickFactory(object):
    def __init__(self):
        """
        Instantiate a SnoBallFactory.
        You shouldn't need to do this; call random_door.randomDoor.getFactory() to get a shared instance.
        """
        self.model = bs.getModel("powerup")
        self.modelSimple = bs.getModel("powerupSimple")

        self.kronkModel = bs.getModel("kronkHead")
        self.kronkModelSimple = bs.getModel("kronkHead")
        self.texKronk = bs.getTexture("kronk")

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
        self.randTex = [self.texTNT, self.texPunch, self.texIceBombs,
                        self.texStickyBombs, self.texImpactBombs, self.texCurse,
                        self.texHealth, self.texLandMines, self.texShield]

        self.brickMaterial = bs.Material()
        self.impactSound = bs.getSound('impactMedium')

        self.brickMaterial.addActions(conditions=(
            ('theyDontHaveMaterial', bs.getSharedObject('playerMaterial')), 'and',
            ('theyHaveMaterial', bs.getSharedObject('objectMaterial')), 'or',
            ('theyHaveMaterial', bs.getSharedObject('footingMaterial'))),
            actions=(
                ('modifyNodeCollision', 'collide', True),
                # ('modifyPartCollision', 'friction', 1)
            ))

        # self.brickMaterial.addActions(conditions=('theyHaveMaterial', bs.getSharedObject('playerMaterial')),
        #                              actions=(
        #                                  ('modifyPartCollision', 'physical', True),
        #                                  ('message', 'ourNode', 'atConnect', changeOwnerMessage())))
        self.brickMaterial.addActions(
            conditions=(
                ('theyHaveMaterial', self.brickMaterial)
            ),
            actions=(('modifyNodeCollision', 'collide', True)))


def weakmethod(method):
    cls = method.im_class
    func = method.im_func
    instance_ref = weakref.ref(method.im_self)
    del method

    def inner(*args, **kwargs):
        instance = instance_ref()

        if instance is None:
            raise ValueError("Cannot call weak method with dead instance")

        return func.__get__(instance, cls)(*args, **kwargs)

    return inner


class BarTooSmallToFinishMessage():
    pass


class ShotProgressBar(bs.Actor):
    def __init__(self, spaz, normalColor=(0.1, 0.5, 0.7),
                 maxColor=(1.0, 0.6, 0.4), maxThreshold=0.9,
                 minRadius=0.2,
                 maxRadius=1.0, timeTakes=400, willDecrease=True,
                 decreaseFinishCallback=None):
        bs.Actor.__init__(self)

        try:
            if spaz is None or spaz.node is None:
                return
        except:
            return

        self.node = bs.newNode('locator', attrs={'shape': 'circle',
                                                 'color': normalColor,
                                                 'opacity': 0.5,
                                                 'drawBeauty': False,
                                                 'additive': True})

        self.maxRadius = maxRadius
        self.minRadius = minRadius
        self.timeTakes = timeTakes
        self.willDecrease = willDecrease
        self.decreaseFinishCallback = decreaseFinishCallback
        self._died = False
        spaz.node.connectAttr('position', self.node, 'position')
        bs.animateArray(self.node, 'size', 1, {0: [2 * minRadius], timeTakes: [2 * maxRadius]})

        arriveMaxTime = int(maxThreshold * timeTakes)
        maxRemainTime = 2 * (timeTakes - arriveMaxTime)

        self.changeColorMaxTimer = bs.Timer(
            arriveMaxTime, bs.WeakCall(self.changeNodeColor, maxColor))

        self.startDecreaseTimer = None
        self.changeColorNormalTimer = None
        self.decreaseFinishTimer = None
        if willDecrease:
            self.changeColorNormalTimer = bs.Timer(
                arriveMaxTime + maxRemainTime, bs.WeakCall(self.changeNodeColor, normalColor))
            self.startDecreaseTimer = bs.Timer(timeTakes + 1, self.doDecrease)
            self.decreaseFinishTimer = bs.Timer(
                2 * (timeTakes + 1), bs.WeakCall(self.handleMessage, BarTooSmallToFinishMessage()))

    def changeNodeColor(self, color):
        self.node.color = color

    def doDecrease(self):
        bs.animateArray(self.node, 'size', 1, {0: [2 * self.maxRadius], self.timeTakes: [2 * self.minRadius]})

    def handleMessage(self, m):
        bs.Actor.handleMessage(self, m)

        if isinstance(m, BarTooSmallToFinishMessage):
            self.handleMessage(bs.DieMessage())
            if self.decreaseFinishCallback:
                self.decreaseFinishCallback()
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())
        elif isinstance(m, bs.DieMessage):
            if self._died: return
            self._died = True
            del self.changeColorMaxTimer
            del self.startDecreaseTimer
            del self.changeColorNormalTimer
            del self.decreaseFinishTimer
            self.node.delete()

    def getProgress(self):
        curRadius = float(self.node.size[0])
        return curRadius / self.maxRadius

    def finishAndGetProgress(self):
        pro = self.getProgress()
        self.handleMessage(bs.DieMessage())
        return pro


class BrickMan(bs.PlayerSpaz):
    def __init__(self, color=(1, 1, 1), highlight=(0.5, 0.5, 0.5), character="Spaz", player=None):
        bs.PlayerSpaz.__init__(self, color=color, highlight=highlight, character=character, player=player)
        self.extras = {}
        self.architectCoolDown = 100
        self.lastDropTime = 0
        self.hitPoints = 1000000
        self.hitPointsMax = 1000000
        self.node.hockey = True

    def onPickUpPress(self):
        return

    def onPickUpRelease(self):
        return

    def architectSetProgressFinish(self):
        # print 'archer callback'
        if 'architectProgress' in self.extras:
            del self.extras['architectProgress']

    def architectSetStart(self):
        if 'architectProgress' in self.extras:
            # 存在计时器正在运行
            return
        nowTime = bs.getGameTime()
        if nowTime - self.lastDropTime < self.architectCoolDown: return
        # self.lastDropTime = nowTime
        self.extras['architectProgress'] = ShotProgressBar(self,
                                                           decreaseFinishCallback=weakmethod(
                                                               self.architectSetProgressFinish
                                                           ),
                                                           timeTakes=400
                                                           ).autoRetain()

    def architectSetStop(self):
        if 'architectProgress' not in self.extras:
            # 不存在计时器正在运行
            return
        nowTime = bs.getGameTime()
        if nowTime - self.lastDropTime < self.architectCoolDown: return
        self.lastDropTime = nowTime
        progress = self.extras['architectProgress'].finishAndGetProgress()
        del self.extras['architectProgress']
        size = ((progress - 0.2) / 0.8) * 3.5 + 0.7
        self.architectDropBrick(size)

    def architectDropBrick(self, brickSize):
        # self.extras['cdBar'] = coolDownBar(self, self.architectCoolDown).autoRetain()
        brickColor = self.getActivity().brickColor
        brickBreakable = self.getActivity().brickBreakable
        brick = Brick(spaz=self, size=brickSize,
                      dieWhenOwnerDie=False, lifeTime=1000 * 1000,
                      color=brickColor, breakable=brickBreakable).autoRetain()

    def initArchitect(self):
        self._punchPowerScale = 1.0
        try:
            self.getPlayer().assignInputCall('punchPress', self.onPunchPress)
            self.getPlayer().assignInputCall('punchRelease', self.onPunchRelease)
            self.getPlayer().assignInputCall('bombPress', self.architectSetStart)
            self.getPlayer().assignInputCall('bombRelease', self.architectSetStop)
            self.getPlayer().assignInputCall('pickUpPress', self.onPickUpPress)
            self.getPlayer().assignInputCall('pickUpRelease', self.onPickUpRelease)
        except Exception, e:
            print e.message


class BrickWorldGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return '砖块世界'

    @classmethod
    def getDescription(cls, sessionType):
        return '在BombSquad中建造自己的小天地\nMOD: Deva\nhttps://superdeva.info/'

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if (issubclass(sessionType, bs.TeamsSession)
                        or issubclass(sessionType, bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls, sessionType):
        maps = copy.copy(bs.getMapsSupportingPlayType("melee"))
        maps.append("Tower D")
        return maps

    @classmethod
    def getSettings(cls, sessionType):
        settings = [("砖块可击碎", {'default': True}),
                    (
                        "color", {'choices': [
                            ('红色', 0), ('绿色', 1),
                            ('蓝色', 2), ('白色', 3),
                            ('紫色', 4), ('黄色', 5),
                            ('黑色', 6), ('随机r', 7)
                        ], 'default': 0}
                    ),
                    ("Respawn Times",
                     {'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0), ('Long', 2.0), ('Longer', 4.0)],
                      'default': 1.0}),
                    ("Epic Mode", {'default': False})]

        return settings

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True

        # print messages when players die since it matters here..
        self.announcePlayerDeaths = True
        allColor = ['red', 'green',
                    'blue', 'white',
                    'purple', 'yellow',
                    'black', 'random']
        self.brickColor = allColor[self.settings['color']]
        self.brickBreakable = self.settings['砖块可击碎']

        # self._scoreBoard = bs.ScoreBoard()

    def getInstanceDescription(self):
        return ('在BombSquad中建造自己的小天地 MOD: Deva\nhttps://superdeva.info/')

    def getInstanceScoreBoardDescription(self):
        return self.getInstanceDescription()

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'ToTheDeath')

    def onTeamJoin(self, team):
        team.gameData['score'] = 0
        if self.hasBegun(): self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(0)
        # self.setupStandardPowerupDrops()
        if len(self.teams) > 0:
            self._scoreToWin = 100000
        else:
            self._scoreToWin = 100000
        self._updateScoreBoard()
        self._dingSound = bs.getSound('dingSmall')

    def spawnPlayer(self, player):

        position = self.getMap().getFFAStartPosition(self.players)
        angle = 20
        name = player.getName()

        lightColor = bsUtils.getNormalizedColor(player.color)
        displayColor = bs.getSafeColor(player.color, targetIntensity=0.75)

        spaz = BrickMan(color=player.color,
                        highlight=player.highlight,
                        character=player.character,
                        player=player)
        player.setActor(spaz)

        spaz.node.name = '建筑师\n'.decode('utf8') + name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        self.scoreSet.playerGotNewSpaz(player, spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(bs.StandMessage(position, angle if angle is not None else random.uniform(0, 360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound, 1, position=spaz.node.position)
        light = bs.newNode('light', attrs={'color': lightColor})
        spaz.node.connectAttr('position', light, 'position')
        bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
        bs.gameTimer(500, light.delete)

        spaz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=True,
                                     enablePickUp=False)
        spaz.playBigDeathSound = True
        spaz.initArchitect()
        return spaz

    def handleMessage(self, m):

        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m)  # augment standard behavior

            player = m.spaz.getPlayer()
            self.respawnPlayer(player)

            killer = m.killerPlayer
            if killer is None: return

            # handle team-kills
            if killer.getTeam() is player.getTeam():

                # in free-for-all, killing yourself loses you a point
                if isinstance(self.getSession(), bs.FreeForAllSession):
                    newScore = player.getTeam().gameData['score'] - 1
                    # if not self.settings['Allow Negative Scores']: newScore = max(0, newScore)
                    player.getTeam().gameData['score'] = newScore

                # in teams-mode it gives a point to the other team
                else:
                    bs.playSound(self._dingSound)
                    for team in self.teams:
                        if team is not killer.getTeam():
                            team.gameData['score'] += 1

            # killing someone on another team nets a kill
            else:
                killer.getTeam().gameData['score'] += 1
                bs.playSound(self._dingSound)
                # in FFA show our score since its hard to find on the scoreboard
                try:
                    killer.actor.setScoreText(str(killer.getTeam().gameData['score']) + '/' + str(self._scoreToWin),
                                              color=killer.getTeam().color, flash=True)
                except Exception:
                    pass

            self._updateScoreBoard()

            # if someone has won, set a timer to end shortly
            # (allows the dust to clear and draws to occur if deaths are close enough)
            if any(team.gameData['score'] >= self._scoreToWin for team in self.teams):
                bs.gameTimer(500, self.endGame)

        else:
            bs.TeamGameActivity.handleMessage(self, m)

    def _updateScoreBoard(self):
        return

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t, t.gameData['score'])
        self.end(results=results)
