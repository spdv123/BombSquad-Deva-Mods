# coding=utf-8
import bs
import copy
import math
import random
import weakref
import bsUtils
import bsVector


def bsGetAPIVersion():
    return 4


def bsGetGames():
    return [JungleHunterGame]


class JungleHunterLanguageChinese():
    gameName = '丛林猎人'
    gameDes = '用你的弓箭猎杀敌人！\n举起键、拳击键调整角度\n长按炸弹键松手射箭！\nMOD: Deva'
    gameScoreDes = '绝不要使用最后一支箭 MOD: Deva'

    getScore1 = u'%s炸死了敌人，+1'
    getScore2 = u'%s击杀了敌人，+2'
    getScore3 = u'%s精准击杀了敌人！+3'
    killSelf = u'%s绝望地自杀了！'
    arrowInit = '初始弓箭数'
    aimHelp = '辅助瞄准'
    spawnDelay = '敌人生成间隔'
    enemyStrength = '敌人强度'

    sNone = '菜鸡'
    sEasy = '简单'
    sNormal = '普通'
    sHard = '困难'
    sNightmare = '噩梦'
    sInvincible = '无敌'


class JungleHunterLanguageEnglish():
    gameName = 'Jungle Hunter'
    gameDes = 'Use arrows to kill the enemies\nPress the PUNCH and PICKUP buttons to adjust the angle\nLong ' \
              'press the BOMB button to CHARGE and release to FIRE\n MOD: Deva'
    gameScoreDes = 'Never use your last arrow. MOD: Deva'

    getScore1 = u'%s killed enemy via blast, get 1 arrow'
    getScore2 = u'%s killed enemy ! get 2 arrows'
    getScore3 = u'%s killed enemy accurately! get 3 arrows'
    killSelf = u'%s committed suicide desperately!'
    arrowInit = 'Arrows you have'
    aimHelp = 'Guided arrow'
    spawnDelay = 'Enemy spawn delay'
    enemyStrength = 'Enemy type'

    sNone = 'None'
    sEasy = 'Easy'
    sNormal = 'Normal'
    sHard = 'Hard'
    sNightmare = 'Nightmare'
    sInvincible = 'Invicible'


JungleHunterLanguage = JungleHunterLanguageChinese


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


class ArrowTouchSpaz(object):
    pass


class ArrowTouchAnything(object):
    pass


class ArrowTouchFootingMaterial(object):
    pass


class HunterArrowFactory(object):
    def __init__(self):
        self.arrowMaterial = bs.Material()

        self.arrowMaterial.addActions(
            conditions=((('weAreYoungerThan', 5), 'or', ('theyAreYoungerThan', 50)),
                        'and', ('theyHaveMaterial', bs.getSharedObject('objectMaterial'))),
            actions=(('modifyNodeCollision', 'collide', False)))

        self.arrowMaterial.addActions(
            conditions=('theyHaveMaterial', bs.getSharedObject('pickupMaterial')),
            actions=(('modifyPartCollision', 'useNodeCollide', False)))

        self.arrowMaterial.addActions(actions=('modifyPartCollision', 'friction', 1))

        self.arrowMaterial.addActions(conditions=('theyHaveMaterial', bs.getSharedObject('playerMaterial')),
                                      actions=(('modifyPartCollision', 'physical', False),
                                               ('message', 'ourNode', 'atConnect', ArrowTouchSpaz())))

        self.arrowMaterial.addActions(conditions=(
            ('theyDontHaveMaterial', bs.getSharedObject('playerMaterial')), 'and',
            ('theyHaveMaterial', bs.getSharedObject('objectMaterial'))),
            actions=('message', 'ourNode', 'atConnect', ArrowTouchAnything()))

        self.arrowMaterial.addActions(conditions=(
            ('theyDontHaveMaterial', bs.getSharedObject('playerMaterial')), 'and',
            ('theyHaveMaterial', bs.getSharedObject('footingMaterial'))),
            actions=('message', 'ourNode', 'atConnect', ArrowTouchFootingMaterial()))


class HunterArrow(bs.Actor):
    def __init__(self, position=(0, 5, 0), velocity=(0, 2, 0), sourcePlayer=None, owner=None,
                 color=(random.random(), random.random(), random.random()), lightRadius=0, allowAim=False):
        bs.Actor.__init__(self)

        factory = self.getFactory()

        self.node = bs.newNode("prop",
                               attrs={'position': position,
                                      'velocity': velocity,
                                      'model': bs.getModel("impactBomb"),
                                      'body': 'sphere',
                                      'colorTexture': bs.getTexture("bunnyColor"),
                                      'modelScale': 0.2,
                                      'isAreaOfInterest': True,
                                      'bodyScale': 0.8,
                                      'materials': [bs.getSharedObject('objectMaterial'), factory.arrowMaterial]
                                      },
                               delegate=self)

        self.sourcePlayer = sourcePlayer
        self.owner = owner
        self._lifeTimer = bs.Timer(8000, bs.WeakCall(self.die))

        self.lightNode = bs.newNode('light',
                                    attrs={'position': position,
                                           'color': color,
                                           'radius': 0.1 + lightRadius,
                                           'volumeIntensityScale': 15.0})

        self.node.connectAttr('position', self.lightNode, 'position')

        self._emit = bs.Timer(15, bs.WeakCall(self.emit), repeat=True)
        self.arrowMag = 5.0
        self.arrowBlast = 0.5
        self._spawnTime = bs.getGameTime()
        self.lifeDist = 0

        self.spawnPos = self.sourcePlayer.actor.node.position

        if allowAim:
            bs.gameTimer(300, bs.WeakCall(self.aimStart))
        self.aimTimer = None

    def aimStart(self):
        if self.node.exists():
            self.aimTimer = bs.Timer(25, self.checkAim, repeat=True)

    def checkAim(self):
        if not self.node.exists():
            self.aimTimer = None
            return

        activity = self.getActivity()
        minDist = 1000.0
        minPos = None
        livingBots = activity._bots.getLivingBots()
        for b in livingBots:
            try:
                dist = self.calcDistance(b.node.position, self.node.position)
                if dist < minDist:
                    minDist = dist
                    minPos = b.node.position
            except:
                pass

        if minPos is not None and minDist < 1.5:
            p1 = minPos
            p2 = self.node.position
            direction = [p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2]]
            self.node.velocity = self.getMaxSpeedByDir(direction)

    @staticmethod
    def getMaxSpeedByDir(direction):
        """
        根据方向确定最大速度
        :param direction: 方向
        :return: 朝这个方向的最大速度
        """
        k = 20.0 / max((abs(x) for x in direction))
        return tuple(x * k for x in direction)

    @staticmethod
    def calcDistance(pos1, pos2):
        return math.sqrt(math.fsum([abs(pos1[k] - pos2[k]) for k in range(3)]))

    def emit(self):
        bs.emitBGDynamics(position=self.node.position, velocity=self.node.velocity, count=4, scale=2, spread=0.1,
                          chunkType='sweat')

    def die(self):
        self.node.handleMessage(bs.DieMessage())

    @classmethod
    def getFactory(cls):
        activity = bs.getActivity()
        if activity is None: raise Exception("no current activity")
        try:
            return activity._sharedArcherArrowFactory
        except Exception:
            f = activity._sharedArcherArrowFactory = HunterArrowFactory()
            return f

    def calcMagByDistance(self):
        endPos = self.node.position
        dist = self.calcDistance(self.spawnPos, endPos)
        self.lifeDist = dist
        # print 'Distance: %f' % dist
        self.arrowMag = 10.0 * dist
        self.arrowBlast = 0.5 * dist

    def handleMessage(self, m):
        bs.Actor.handleMessage(self, m)
        if isinstance(m, ArrowTouchAnything):
            node = bs.getCollisionInfo("opposingNode")

            if node is not None and node.exists():
                v = self.node.velocity
                t = self.node.position
                hitDir = self.node.velocity
                m = self.node
                self.calcMagByDistance()
                node.handleMessage(bs.HitMessage(pos=t,
                                                 velocity=v,
                                                 magnitude=self.arrowMag,
                                                 velocityMagnitude=self.arrowMag,
                                                 radius=0,
                                                 srcNode=self.node,
                                                 sourcePlayer=self.sourcePlayer,
                                                 forceDirection=hitDir))

            self.node.handleMessage(bs.DieMessage())

        elif isinstance(m, bs.DieMessage):
            if self.node.exists():
                velocity = self.node.velocity
                explosion = bs.newNode("explosion",
                                       attrs={'position': self.node.position,
                                              'velocity': (velocity[0], max(-1.0, velocity[1]), velocity[2]),
                                              'radius': 1,
                                              'big': False})
                bs.playSound(sound=bs.getSound(random.choice(['impactHard', 'impactHard2', 'impactHard3'])),
                             position=self.node.position)
                self.node.delete()
                self.lightNode.delete()
                self._emit = None

        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())

        elif isinstance(m, bs.HitMessage):
            self.node.handleMessage("impulse", m.pos[0], m.pos[1], m.pos[2],
                                    m.velocity[0], m.velocity[1], m.velocity[2],
                                    1.0 * m.magnitude, 1.0 * m.velocityMagnitude, m.radius, 0,
                                    m.forceDirection[0], m.forceDirection[1], m.forceDirection[2])

        elif isinstance(m, ArrowTouchSpaz):
            node = bs.getCollisionInfo("opposingNode")
            if node is not None and node.exists():
                # node.handleMessage(bs.FreezeMessage())

                v = self.node.velocity
                t = self.node.position
                hitDir = self.node.velocity

                self.calcMagByDistance()
                hitType = 'hunter'
                if self.lifeDist > 5:
                    hitType = 'hunterGod'
                    # self.sourcePlayer.actor.setScoreText('狙击精英')
                node.handleMessage(bs.HitMessage(pos=t,
                                                 velocity=(10, 10, 10),
                                                 magnitude=self.arrowMag,
                                                 velocityMagnitude=self.arrowMag,
                                                 radius=0,
                                                 srcNode=self.node,
                                                 sourcePlayer=self.sourcePlayer,
                                                 forceDirection=hitDir,
                                                 hitType=hitType))

            self.node.handleMessage(bs.DieMessage())

        elif isinstance(m, ArrowTouchFootingMaterial):
            self.calcMagByDistance()
            bs.Blast(position=self.node.position,
                     velocity=self.node.velocity,
                     blastRadius=self.arrowBlast, blastType='normal',
                     sourcePlayer=self.sourcePlayer, hitType='hunterBlast').autoRetain()
            self.handleMessage(bs.DieMessage())
            # bs.playSound(sound=bs.getSound("blip"), position=self.node.position)
        elif isinstance(m, bs.PickedUpMessage):
            self.handleMessage(bs.DieMessage())


class KillerGetScoreMessage(object):
    def __init__(self, killer, score):
        self.killer = killer
        self.score = score
        if score == 3:
            self.text = JungleHunterLanguage.getScore3 % killer.getName()
        elif score == 2:
            self.text = JungleHunterLanguage.getScore2 % killer.getName()
        else:
            self.text = JungleHunterLanguage.getScore1 % killer.getName()


class PreyBot(bs.SpazBot):
    def __init__(self):
        bs.SpazBot.__init__(self)
        self.hitPoints = self._activity().settings[JungleHunterLanguage.enemyStrength]
        self.hitPointsMax = self.hitPoints
        self.killer = None
        self.killerPoints = 0

    def handleMessage(self, m):
        if isinstance(m, bs.HitMessage):
            if m.sourcePlayer is not None and m.sourcePlayer.exists():
                if m.hitType == 'hunter':
                    self.killer = m.sourcePlayer
                    self.killerPoints = 2
                elif m.hitType == 'hunterGod':
                    self.killer = m.sourcePlayer
                    self.killerPoints = 3
                elif m.hitType == 'hunterBlast':
                    self.killer = m.sourcePlayer
                    self.killerPoints = 1
        elif isinstance(m, bs.DieMessage):
            if not self._dead and not m.immediate:
                if self.killer is not None and self.killerPoints > 0:
                    self._activity().handleMessage(KillerGetScoreMessage(
                        self.killer, self.killerPoints))
        bs.SpazBot.handleMessage(self, m)


class NinjaPrey(PreyBot):
    punchiness = 1.0
    chargeDistMin = 10.0
    chargeDistMax = 9999.0
    chargeSpeedMin = 1.0
    chargeSpeedMax = 1.0
    throwDistMin = 9999
    throwDistMax = 9999
    defaultShields = False
    defaultBoxingGloves = False

    def __init__(self):
        random.seed()
        self.pointsMult = random.choice([1, 2, 3, 2])
        self.run = random.choice([True, False])
        self.character = random.choice(['Santa Claus',
                                        'Easter Bunny',
                                        'B-9000',
                                        'Kronk',
                                        'Zoe',
                                        'Taobao Mascot',
                                        'Pascal',
                                        'Snake Shadow',
                                        'Mel',
                                        'Bernard',
                                        'Pixel',
                                        'Frosty',
                                        'Agent Johnson',
                                        'Bones',
                                        'Jack Morgan'])
        PreyBot.__init__(self)


class HunterSpaz(bs.PlayerSpaz):
    def __init__(self, color=(1, 1, 1), highlight=(0.5, 0.5, 0.5), character="Spaz", player=None, force_fly=False,
                 allowAim=False):
        if player is None: return
        bs.PlayerSpaz.__init__(self,
                               color=color,
                               highlight=highlight,
                               character=character,
                               player=player)
        self.extras = {}
        self.archerCoolDown = 0
        self.lastDropTime = -10000
        self.hitPointsMax = self.hitPoints = 3000

        self.shotAngle = 40
        self.isUpPressing = False
        self.isDownPressing = False
        self.allowAim = allowAim

        if force_fly:
            self.node.fly = True

        self.updateShotAngleTimer = bs.Timer(20, bs.WeakCall(self.updateShotAngle), repeat=True)

    def updateShotAngle(self):
        if self.isUpPressing:
            self.shotAngle = min(self.shotAngle + 1, 80)
        if self.isDownPressing:
            self.shotAngle = max(self.shotAngle - 1, 10)
        self.setScoreText(str(self.shotAngle) + '°', color=(1, 1, 0.4))

    @DeprecationWarning
    def onMoveUpDownDeprecated(self, value):
        if not self.node.exists(): return
        threshold = 0.7
        if value < -threshold:
            self.isDownPressing = True
            self.isUpPressing = False
        elif value > threshold:
            self.isDownPressing = False
            self.isUpPressing = True
        else:
            self.isDownPressing = False
            self.isUpPressing = False

    def onPickUpPress(self):
        self.isUpPressing = True

    def onPickUpRelease(self):
        self.isUpPressing = False

    def onPunchPress(self):
        self.isDownPressing = True

    def onPunchRelease(self):
        self.isDownPressing = False

    def archerShotProgressFinish(self):
        # print 'archer callback'
        if 'archerProgress' in self.extras:
            del self.extras['archerProgress']

    def noMoreArrows(self):
        if self.sourcePlayer.getTeam().gameData['arrows'] <= 0:
            return True
        return False

    def archerShotArrowStart(self):
        if self.noMoreArrows(): return
        if 'archerProgress' in self.extras:
            # 存在计时器正在运行
            return
        nowTime = bs.getGameTime()
        if nowTime - self.lastDropTime < self.archerCoolDown: return
        # self.lastDropTime = nowTime
        self.extras['archerProgress'] = ShotProgressBar(self,
                                                        decreaseFinishCallback=weakmethod(
                                                            self.archerShotProgressFinish
                                                        )
                                                        ).autoRetain()

    def archerShotArrowStop(self):
        if self.noMoreArrows(): return
        if 'archerProgress' not in self.extras:
            # 不存在计时器正在运行
            return
        nowTime = bs.getGameTime()
        if nowTime - self.lastDropTime < self.archerCoolDown: return
        self.lastDropTime = nowTime
        progress = self.extras['archerProgress'].finishAndGetProgress()
        del self.extras['archerProgress']
        v1 = (progress - 0.2) / 0.8
        self.archerRealShot(v1)

    def archerRealShot(self, v1=0.5):
        if self.noMoreArrows(): return
        self.sourcePlayer.getTeam().gameData['arrows'] -= 1
        if self.noMoreArrows():
            for p in self.sourcePlayer.getTeam().players:
                if p.isAlive() and p.actor.exists():
                    bs.screenMessage(JungleHunterLanguage.killSelf % p.getName())
                    p.actor.handleMessage(bs.DieMessage())
            self._activity()._updateScoreBoard()
            self._activity()._checkEndGame()
            return
        self._activity()._updateScoreBoard()
        p1 = self.node.positionCenter
        p2 = self.node.positionForward
        direction = [p1[0] - p2[0], p2[1] - p1[1], p1[2] - p2[2]]
        direction[1] = 0.0
        dirSig = -1 if direction[0] < 0 else 1

        # print 'Dir', direction
        # print math.sqrt(direction[0] * direction[0] + direction[2] * direction[2])

        angle = self.shotAngle * 2.0 * math.pi / 360.
        if self.node.fly:
            vel = [10 * v1 * math.cos(angle) * dirSig, 10 * v1 * math.sin(angle), 0.0]
        else:
            v_ground = 10 * v1 * math.cos(angle)
            d0 = direction[0] / 0.20
            d2 = direction[2] / 0.20
            vel = [d0 * v_ground, 10 * v1 * math.sin(angle), d2 * v_ground]
        # print 'vel', vel
        HunterArrow(position=self.node.position,
                    velocity=tuple(vel),  # (vel[0] * 2, vel[1] * 2 + v1, vel[2] * 2),
                    owner=self.getPlayer(),
                    sourcePlayer=self.getPlayer(),
                    color=self.node.color,
                    allowAim=self.allowAim).autoRetain()

    def initArcher(self):
        self._punchPowerScale = 1.0
        try:
            self.getPlayer().assignInputCall('punchPress', self.onPunchPress)
            self.getPlayer().assignInputCall('punchRelease', self.onPunchRelease)
            self.getPlayer().assignInputCall('bombPress', self.archerShotArrowStart)
            self.getPlayer().assignInputCall('bombRelease', self.archerShotArrowStop)
            self.getPlayer().assignInputCall('pickUpPress', self.onPickUpPress)
            self.getPlayer().assignInputCall('pickUpRelease', self.onPickUpRelease)
        except Exception, e:
            print e.message


class JungleHunterGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return JungleHunterLanguage.gameName

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName': 'Survived',
                'scoreType': 'milliseconds',
                'scoreVersion': 'B'}

    @classmethod
    def getDescription(cls, sessionType):
        return JungleHunterLanguage.gameDes

    def getInstanceScoreBoardDescription(self):
        return JungleHunterLanguage.gameScoreDes + ". " + self.getSelectedHard()

    @classmethod
    def getSupportedMaps(cls, sessionType):
        # return ['Rampage']
        return bs.getMapsSupportingPlayType("melee")

    def getSelectedHard(self):
        strength = self.settings[JungleHunterLanguage.enemyStrength]
        strength = {300: JungleHunterLanguage.sNone,
                    600: JungleHunterLanguage.sEasy,
                    1000: JungleHunterLanguage.sNormal,
                    1700: JungleHunterLanguage.sHard,
                    5000: JungleHunterLanguage.sNightmare,
                    1000000: JungleHunterLanguage.sInvincible}.get(strength, JungleHunterLanguage.sNone)
        return strength

    @classmethod
    def getSettings(cls, sessionType):
        return [(JungleHunterLanguage.arrowInit, {'minValue': 2, 'default': 10, 'increment': 1}),
                (JungleHunterLanguage.spawnDelay, {'minValue': 1, 'default': 12, 'increment': 1}),
                (JungleHunterLanguage.aimHelp, {'default': False}),
                (JungleHunterLanguage.enemyStrength, {'choices': [(JungleHunterLanguage.sNone, 300),
                                                                  (JungleHunterLanguage.sEasy, 600),
                                                                  (JungleHunterLanguage.sNormal, 1000),
                                                                  (JungleHunterLanguage.sHard, 1700),
                                                                  (JungleHunterLanguage.sNightmare, 5000),
                                                                  (JungleHunterLanguage.sInvincible, 1000000)],
                                                      'default': 1000}),
                ("Epic Mode", {'default': False})]

    # we support teams, free-for-all, and co-op sessions
    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if (issubclass(sessionType, bs.TeamsSession)
                        or issubclass(sessionType, bs.FreeForAllSession)
                        or issubclass(sessionType, bs.CoopSession)) else False

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)

        if self.settings['Epic Mode']: self._isSlowMotion = True
        self._maxArrows = self.settings[JungleHunterLanguage.arrowInit] * 2

        # print messages when players die (since its meaningful in this game)
        self.announcePlayerDeaths = True

        self._lastPlayerDeathTime = None
        self.positionSpan = None
        self._scoreBoard = bs.ScoreBoard()

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['arrows'], self._maxArrows)

    # called when our game is transitioning in but not ready to start..
    # ..we can go ahead and set our music and whatnot
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')

    def onTeamJoin(self, team):
        team.gameData['arrows'] = self._maxArrows / 2
        if self.hasBegun(): self._updateScoreBoard()

    # called when our game actually starts
    def onBegin(self):

        bs.TeamGameActivity.onBegin(self)

        # bs.gameTimer(t,self._decrementMeteorTime,repeat=True)

        # kick off the first wave in a few seconds
        t = self.settings[JungleHunterLanguage.spawnDelay] * 1000
        if self.settings['Epic Mode']: t /= 4
        # bs.gameTimer(t,self._setMeteorTimer)

        self._timer = bs.OnScreenTimer()
        self._timer.start()
        self._updateScoreBoard()

        bs.gameTimer(4000, self._checkEndGame)  # 4秒之后检测一波

        self._bots = bs.BotSet()
        bs.gameTimer(1000,
                     bs.Call(self._bots.spawnBot, NinjaPrey, pos=self.getMap().getFFAStartPosition(self.players),
                             spawnTime=100), repeat=False)

        bs.gameTimer(t, bs.WeakCall(self.botsGener), repeat=True)

    def botsGener(self):
        self._bots.spawnBot(NinjaPrey, pos=self.getRandomPosition(self), spawnTime=100)

    # overriding the default character spawning..
    def spawnPlayer(self, player):
        position = self.getMap().getFFAStartPosition(self.players)
        angle = 20
        name = player.getName()

        lightColor = bsUtils.getNormalizedColor(player.color)
        displayColor = bs.getSafeColor(player.color, targetIntensity=0.75)

        spaz = HunterSpaz(color=player.color,
                          highlight=player.highlight,
                          character=player.character,
                          player=player,
                          force_fly=False,
                          allowAim=self.settings[JungleHunterLanguage.aimHelp])
        player.setActor(spaz)

        spaz.node.name = name
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

        # lets reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up
        spaz.connectControlsToPlayer(enablePunch=False,
                                     enableBomb=True,
                                     enablePickUp=False)
        spaz.initArcher()
        spaz.playBigDeathSound = True

        return spaz

    def getRandomPosition(self, activity):
        if self.positionSpan is not None:
            ru = random.uniform
            ps = self.positionSpan
            return (ru(ps[0][0] - 1.0, ps[0][1] + 1.0), ps[1][1] + ru(0.1, 1.5), ru(ps[2][0] - 1.0, ps[2][1] + 1.0))

        pts = copy.copy(activity.getMap().ffaSpawnPoints)
        pts2 = activity.getMap().powerupSpawnPoints
        for i in pts2:
            pts.append(i)
        pos = [[999, -999], [999, -999], [999, -999]]
        for pt in pts:
            for i in range(3):
                pos[i][0] = min(pos[i][0], pt[i])
                pos[i][1] = max(pos[i][1], pt[i])

        self.positionSpan = pos
        # print repr(pos)
        return self.getRandomPosition(activity)

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
        elif isinstance(m, KillerGetScoreMessage):
            bs.screenMessage(m.text,
                             top=True, color=m.killer.color,
                             image=m.killer.getIcon())
            m.killer.getTeam().gameData['arrows'] = min(
                m.killer.getTeam().gameData['arrows'] + m.score, self._maxArrows)
            self._updateScoreBoard()
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

        # mark 'death-time' as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:

                # throw an extra fudge factor +1 in so teams that
                # didn't die come out ahead of teams that did
                if 'deathTime' not in player.gameData: player.gameData['deathTime'] = curTime + 1

                # award a per-player score depending on how many seconds they lasted
                # (per-player scores only affect teams mode; everywhere else just looks at the per-team score)
                score = (player.gameData['deathTime'] - self._timer.getStartTime()) / 1000
                if 'deathTime' not in player.gameData: score += 50  # a bit extra for survivors
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
