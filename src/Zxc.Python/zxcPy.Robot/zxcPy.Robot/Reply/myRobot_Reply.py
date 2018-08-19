#-*- coding: utf-8 -*-
"""
Created on  张斌 2017-11-17 12:16:00 
    @author: zhang bin
    @email:  zhangbin@gsafety.com

    Python的Robot消息处理接口(文本消息)
"""
import os, ast, time, threading  
import mySystem 
    
#引用根目录类文件夹--必须，否则非本地目录起动时无法找到自定义类
mySystem.Append_Us("../Prjs", False, __file__)
mySystem.Append_Us("../Roots", False, __file__)
mySystem.Append_Us("", False)    
import myWeb, myImport, myData, myData_Trans, myDebug, myIO, myManager_Msg
import myRoot, myRoot_Usr

#初始全局消息管理器
from myGlobal import gol 
gol._Init()     #先必须在主模块初始化（只在Main模块需要一次即可）


#机器人消息处理工厂类（所有消息从此处走）
class myRobot_Reply():
    def __init__(self): 
        self.usrTag = ""
        self.usrName = ""
        self.usrNameNick = ""
        self.usrReplys = myRoot_Usr.myRoot_Usrs("", "")   #消息用户集
        self.usrMMsg = gol._Get_Setting('manageMsgs')     #消息管理器
        self.usrMQ_Recv = None   #消息队列队形      
        self.isRunning = False   #是否运行中
        self._Init()             #按全局权限初始
        #self.wxDos = {}         #消息处理类
        #self.wxUser_Root = None #当前授权用户对象(避免频繁查找)
        myDebug.Print("消息处理工厂--已初始 (%s::%s--%s)" % (self.usrName, self.usrNameNick, self.usrTag))
    def _Init(self): 
        #初始用户全局功能权限对象 
        self.root = gol._Get_Value('rootRobot')     #权限信息
        if(self.root != None):
            self.usrName = self.root.usrName
            self.usrNameNick =self.root.usrNameNick
            self.usrTag =self.root.usrID
            self.usrReplys = myRoot_Usr.myRoot_Usrs(self.usrName, self.usrTag)   #消息用户集 
            
        #初始根目录信息
        strDir, strName = myIO.getPath_ByFile(__file__)
        self.Dir_Base = os.path.abspath(os.path.join(strDir, "../.."))  
        self.Dir_LogMsg = self.Dir_Base + "/Log/Msgs/"
        self.usrMMsg.Init_LogDir(self.Dir_LogMsg)   #初始日志路径
        
    #处理封装返回消息(按标识内容处理)
    def Done_ByMsg(self, msg, bOnHandleMsg = False):
        myDebug.Print("请求消息:: ", msg)
        if(msg == None): return None

        #提取消息内容（自定义格式类型 myManager_Msg.OnCreatMsg）
        usrID = msg.get('usrID', "")
        usrName = msg.get('usrName', "")
        usrNameNick = msg.get('usrNameNick', "")
        nameSelf = msg.get('usrNameSelf', "")
        groupID = msg.get('groupID', "")
        groupName = msg.get('groupName', "")

        msgText = msg.get('msg', "")
        msgID = msg.get('msgID', "")
        msgType = msg.get('msgType', "")
        plat = msg.get('plat', "")

        #按消息类型进一步处理('TEXT', 'IMAGE', 'VOICE', 'VIDEO')
        if(msgType == myManager_Msg.myMsgType.TEXT):
            msgText = msgText
        else:
            return None 

        #调用 
        msgR = self.Done(usrID, usrName, usrNameNick, msgText, msgID, msgType, plat, groupID, groupName, nameSelf)
        myDebug.Debug("处理消息::", msgR)  

        #推送结果至消息管理器 
        if(bOnHandleMsg):   
            self.OnHandleMsg(msgR)      #消息处理
        return msgR
    #按命令处理返回消息(按标识内容处理)
    def Done(self, usrID, usrName, nickName, strText, msgID = "", msgType = 'TEXT', usrPlant = "", idGroup = "", nameGroup = "", nameSelf = ""):
        #命令识别
        pPrj = None 
        pUser = None 
        pGroup = None
        bIsRegist = False
        if(strText[0:2] == "@@"):
            pPrj, pUser, bIsRegist = self._Create_Cmd(usrID, usrName, nickName, strText[2:], usrPlant, idGroup, nameGroup, nameSelf, True)
        else:
            #查找用户
            pUser = self._Find_Usr(usrID, usrName, nickName, "", usrPlant)
      
        #查找用户, 调用消息处理方法调用
        if(pUser != None):
            if(nameGroup != ""):               
                pGroup = self._Find_Group(idGroup, usrID, usrName, nickName, usrPlant)   
            msgR = pUser.Done(pPrj, strText, msgID, msgType, usrPlant, pGroup, nameSelf, bIsRegist) 
            return msgR
        return None
     
    #消息处理
    def OnHandleMsg(self, msg):  
        if(msg == None): return None
        
        #必须有处理消息存在
        strMsg = msg.get('msg', "")
        if(strMsg != ""):
            #尾部标签
            strTag = "  --zxcRobot  " + myData_Trans.Tran_ToTime_str(None, '%H:%M:%S')
            strTag = (32 - len(strTag)) * " " + strTag
            msg["msg"] = strMsg + "\n" + strTag

            #消息管理器处理消息
            self.usrMMsg.OnHandleMsg(msg)
        
    #运行-开始
    def Start(self):
        self.isRunning = True
    #运行-停止
    def Stop(self):
        self.isRunning = False

    #查找用户（不存在则自动创建）
    def _Find_Usr(self, usrID, usrName, usrName_Nick, usrID_sys = "", usrPlant = ""): 
        #按消息生成对应对象 
        pUser = self.root.usrInfos._Find(usrID, usrName, usrName_Nick, usrID_sys, usrPlant, False)
        if(pUser == None or len(pUser.usrPrj.prjDos) < 1):      #非参与用户，于全局用户集信息提取，不存在的自动生成
            pUser = self.root.usrInfos._Find(usrID, usrName, usrName_Nick, usrID_sys, usrPlant, True)
            pUser.usrPrj._Add_prjDos(self.root.rootPrjs)
            self.usrReplys._Add(pUser)
        return pUser
    def _Find_Group(self, idGroup, nameGroup, usrPlant = ""): 
        #按消息生成对应对象 
        pGroup = self.root.usrGroups.Find_Group(idGroup, nameGroup, usrPlant, False)
        return pGroup
    #是否管理员账户（直接提升权限）
    def _IsRoot_Usr(self, usrName):
        pRoot = self.wxRoot.prjRoots_user.get(usrName.lower()) 
        if pRoot == None : return False
        if pRoot.prjRoot == None : return False
        return True
    #是否可启动命令用户
    def _IsEnable_Usr(self, pUser, pPrj, isGroup, pGroup = None, isCommand = False):
        #必须可用
        bRigist = False
        if(pPrj.IsEnable() == False): return False, bRigist

        #区分是否运行状态，非运行，必须root用户启用
        bIsRoot = pPrj.IsRoot_user(pUser)   #查找用户权限 
        if(pPrj.IsRunning() == False):      #命令必须权限用户启用 
            if(isCommand and bIsRoot == False): 
                return False, bRigist       #启动命令必须权限用户 
        else:   #运行时，仅非统一启动时，需要个人启动
            if(pPrj.IsEnable_All() == False): return False, bRigist
            if(isCommand and bIsRoot == False):
                bRigist = True              #标识为注册
                
        #群有效区分
        if(isGroup):                        #群有效，且为设置群
            return pPrj.IsEnable_group(pGroup), bRigist
        else:
            return pPrj.IsEnable_one(), bRigist  #单人有效(一对一)
            
    #命令处理（@@命令，一次开启，再次关闭） 
    def _Create_Cmd(self, usrID, usrName, nickName, prjCmd, usrPlant = "", idGroup = "", nameGroup = "", nameSelf = "", isCommand = False):    
        #查找功能权限对象
        pPrj = self.root.rootPrjs._Find(prjCmd)
        if(pPrj == None):
            print(">>Create Prj(%s) Faield" % (prjCmd))
            return None, None, False
        if(pPrj.IsEnable() == False): return None, None, False      #必须启用

        #查找用户（功能开启全部可用则当前用户）  
        pGroup = self._Find_Group(idGroup, nameGroup, usrPlant)   
        pUser = self._Find_Usr(usrID, usrName, nickName, "", usrPlant)   
        if(pUser == None): return None, pUser, False
        
        #功能权限验证 
        isGroup = nameGroup != ""
        bEnable, bRigist = self._IsEnable_Usr(pUser, pPrj, isGroup, pGroup, isCommand)
        if(bEnable == False): return None, pUser, False             #必须可用

        #功能注册用户
        #if(isSelf):
        #    if(isCommand == False and pPrj.startUser == usrName):
        #        return None, None, False
        #    pPrj.registUser(usrID, "", nickName, idGroup)


        #动态实例 (非单例，单独实例并缓存) 
        if(pPrj.IsRunSingle() == False):      
            prjClass = pPrj.creatIntance()          #实例对象--专有      
            prjClass.isRunning = pPrj.isRunning     #同步运行状态
            pUser.usrPrj._Change_prjDo(prjClass)    #切换功能 
        return pPrj, pUser, bRigist  
     

#主启动程序
if __name__ == "__main__":
    #sys.path.append("C:\Python35-32\Lib\site-packages\myPy_Libs")

    #动态实例测试
    pWxdo2 = myImport.Import_Class("myRobot_Repeater","myRobot_Repeater")('zxc', 'zxcID');
    myDebug.Debug( pWxdo2.Done("@@Repeater"))
    myDebug.Debug( pWxdo2.Done("Hello"))
    myDebug.Debug( pWxdo2.Done("Bye"))
    myDebug.Debug( pWxdo2.Done("@@Repeater"))
    print("\n\n")

    #机器人消息处理
    pWxReply = myRobot_Reply()
    pWxReply._Init()
    
    #用户信息
    usrID = "zxc_0"
    usrName = "墨紫"
    nickName = ""
    usrPlant = "wx"
    msgType = "TEXT"
    msgID = ""

    
    #复读机功能测试
    pWxReply.Done(usrID, usrName, nickName, '@@Repeater', msgID, msgType, usrPlant)
    myDebug.Debug(pWxReply.Done(usrID, usrName, nickName, 'Hello Rep', msgID, msgType, usrPlant))
    myDebug.Debug(pWxReply.Done(usrID, usrName, nickName, 'zxczxc', "@zxcvbnm", msgType, usrPlant))
    myDebug.Debug(pWxReply.Done(usrID, usrName, nickName, 'Bye Repeater', msgID, msgType, usrPlant))
    pWxReply.Done(usrID, usrName, nickName, '@@Repeater', msgID, msgType, usrPlant) 
    print()

    #复读功能再次开启与关闭
    pWxReply.Done(usrID, usrName, nickName, '@@Repeater', msgID, msgType, usrPlant) 
    pWxReply.Done(usrID, usrName, nickName, '@@Repeater', msgID, msgType, usrPlant)  
    print()


    #聊天机器人测试
    pWxReply.Done(usrID, usrName, nickName, '@@ChatRobot', msgID, msgType, usrPlant) 
    myDebug.Debug(pWxReply.Done(usrID, usrName, nickName, 'Hello Robot', msgID, msgType, usrPlant))
    myDebug.Debug(pWxReply.Done(usrID, usrName, nickName, 'God Job...', msgID, msgType, usrPlant))
    myDebug.Debug(pWxReply.Done(usrID, usrName, nickName, 'Bye Robot', msgID, msgType, usrPlant))
    pWxReply.Done(usrID, usrName, nickName, '@@ChatRobot', msgID, msgType, usrPlant) 
    print()


    #交互启动测试 
    pWxReply.Done(usrID, usrName, nickName, '@@Repeater', msgID, msgType, usrPlant) 
    pWxReply.Done(usrID, usrName, nickName, '@@ChatRobot', msgID, msgType, usrPlant) 
    myDebug.Debug(pWxReply.Done(usrID, usrName, nickName, 'Hello ChatRobot...', msgID, msgType, usrPlant))
    print()
    myDebug.Print("Change user")
    
   #队列消息测试
    if(True == True):  
        #循环测试
        nTimes = 5
        pMMsg = myManager_Msg.myManager_Msg()
        msg = pMMsg.OnCreatMsg()
        msg["usrID"] = usrID
        msg["usrName"] = "茶叶一主号"     
        msg["usrNameNick"] = ""     
        msg["plat"] = usrPlant
        msg["msg"] = "@@ChatRobot" 

        #启动自己功能
        myDebug.Debug(pWxReply.Done_ByMsg(msg, True))
        time.sleep(0.1) 
        for x in range(0, nTimes):
            #发送消息
            msg["msg"] = "hello world " + str(x)
            pWxReply.Done_ByMsg(msg, True)
            time.sleep(0.01) 

    time.sleep(2) 
    pWxReply.Done(usrID, usrName, nickName, '@@ChatRobot', msgID, msgType, usrPlant) 
    print()



    #消息提取测试
    #pMsg = pR.msgLogs._Find_Log("zxcID").Find("@zxcvbnm")

    exit()

 
 
