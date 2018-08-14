# -*- coding: utf-8 -*-
"""
Created on  张斌 2018-07-23 11:00:00 
    @author: zhang bin
    @email:  zhangbin@gsafety.com

    消息处理器--通用消息处理器
"""
import sys, os, copy, datetime
import myEnum, myDebug, myWeb_urlLib, myMQ_Rabbit #, myVoice 


#定义消息类型枚举
myMsgType = myEnum.enum('TEXT', 'IMAGE', 'VOICE', 'VIDEO')
myMsgPlat = myEnum.enum('wx')

#自定义消息对象
class myMsg():
    def __init__(self, msg, msgID, msgType = myMsgType.TEXT): 
        self.msg = msg              #消息内容
        self.msgID = msgID          #消息标识
        self.msgType = msgType      #消息类型
        self.msgUrl = ""            #消息链接(多媒体)
        self.msgTime = datetime.datetime.now()  #消息示例时间 
#自定义消息对象集
class myMsgs():
    def __init__(self, usrName, usrNameNick, userID): 
        self.usrName = usrName          #归属用户
        self.usrNameNick = usrNameNick  #归属用户
        self.userID = userID            #归属用户ID
        self.usrID_sys = userID         #归属用户ID_sys
        self.usrMsgs = []               #消息集

    #添加消息
    def Add(self, msg, msgID = '', msgType = myMsgType.TEXT):
        if(msg == ""): return False
        pMsg = myMsg(msg, msgID, msgType)
        return self._Add(pMsg)
    def _Add(self, msg):
        if(msg == None): return False
        self.usrMsgs.append(msg)
        return True
    
    #查找消息
    def Find(self, msgID):
        nLen = len(self.usrMsgs)
        for ind in range(nLen - 1, -1, -1):
            pMsg = self.usrMsgs[ind]
            if(pMsg.msgID == msgID):
                return pMsg
        return None

#消息处理器--通用消息处理器
class myManager_Msg():
    def __init__(self, msgUrls ={myMsgPlat.wx: "http://127.0.0.1:8666/zxcAPI/weixin"}):
        self.usePrint = True
        self.useVoice = False
        self.useLineMsg = True
        self.useMqMsg = True
        self.msgExramp = {"usrID":'', "usrName":'', "usrNameNick":'', "msg":'', "msgID":'', "msgType":'TEXT', "groupID":'', "plat":''} #消息样例
        self.msgLogs = {}
        self.msgInd_Name = {}
        self.msgInd_Nick = {}
        
        self.usrWebs = {}           #在线消息集    
        if(self.useLineMsg):
            keys = msgUrls.keys()
            for x in keys:          #按消息分类标识初始对应web对象并存入dict
                pWeb = myWeb_urlLib.myWeb(msgUrls[x])
                self.usrWebs[x] = pWeb
                
        self.usrMQs = {}            #消息队列     
        if(self.useMqMsg):
            keys = msgUrls.keys()
            for x in keys:          #按消息分类标识初始对应web对象并存入dict
                #初始消息发送队列
                usrMQ_Name = str(myMsgPlat.wx)
                usrMQ_Name = 'zxcMQ_' + usrMQ_Name[0:1].upper() + usrMQ_Name[1:]
                usrMQ = myMQ_Rabbit.myMQ_Rabbit(True)
                usrMQ.Init_Queue(usrMQ_Name, True, True)
                self.usrMQs[x] = usrMQ
        
    #添加消息
    def Log(self, usrID, usrName, usrNameNick, msg, msgID, msgType = myMsgType.TEXT):
        if(usrID == ""): return False
        pMsgs = self._Find_Log(usrID, usrName, usrNameNick, True)
        if(pMsgs != None):
            if(msg == ""): return False
            pMsg = myMsg(msg, msgID, msgType)
            pMsgs._Add(pMsg) 
        return True
    def _Log(self, msg = {}):
        usrID = msg.get('usrID', "")
        if(usrID == ""): return False
        usrName = msg.get('usrName', "")
        usrNameNick = msg.get('usrNameNick', "")
        return self.Log(usrID, usrName, usrNameNick, msg.get('msg', ""), msg.get('msgID', ""), msg.get('msgType', ""))
    def _Find_Log(self, usrID, usrName = "", usrNameNick = "", bCreatAuto = True):
        pMsgs = self.msgLogs.get(usrID, None)
        if(pMsgs == None):
            pMsgs = self.msgInd_Name.get(usrName, None)
            if(pMsgs == None):
                pMsgs = self.msgInd_Nick.get(usrNameNick, None)

        #创建新消息集
        if(pMsgs == None and bCreatAuto):
            pMsgs = myMsgs(usrName, usrNameNick, usrID)
            self.msgLogs[usrID] = pMsgs
            if(usrName != ""): self.msgInd_Name[usrName] = usrID
            if(usrNameNick != ""): self.msgInd_Nick[usrNameNick] = usrID
        return pMsgs

    #消息处理
    def OnHandleMsg(self, msg):
        strMsg = msg.get('msg')

        #文字输出
        if(self.usePrint): myDebug.Print("消息管理器::", strMsg)

        #声音输出
        #if(self.useVoice):
        #    myVoice.Say_thrd(msg["text"])

        #在线消息输出
        typePlatform = msg.get("plat", myMsgPlat.wx)
        if(typePlatform != ""):
            pWeb = self.usrWebs.get(typePlatform, None)     #提取对应平台的web对象
            if(pWeb != None):   
                #格式化接口输出
                wxPath = msg["usrName"] + "/" + strMsg + "/" + msg["msgType"]
                pWeb.Do_API_get(wxPath, typePlatform + "API-py")

            usrMQ = self.usrMQs.get(typePlatform, None)
            if(usrMQ != None):
                usrMQ.Send_Msg(usrMQ.nameQueue, msg)

    #创建新消息
    def OnCreatMsg(self):
        return copy.deepcopy(self.msgExramp)
              
#初始全局消息管理器
from myGlobal import gol 
gol._Init()     #先必须在主模块初始化（只在Main模块需要一次即可）
gol._Set_Setting('manageMsgs', myManager_Msg())


if __name__ == '__main__':
   pMMsg = gol._Get_Setting('manageMsgs')

   #组装消息 
   msg = {}
   msg["usrName"] = "茶叶一主号"
   msg["usrID"] = "zxcID"
   msg["msg"] = "测试消息py"
   msg["msgID"] = "msgID-***"
   msg["msgType"] = "TEXT"
   msg["plat"] = "weixin"
   pMMsg.OnHandleMsg(msg)


   #消息日志
   pMMsg.Log("zxcID", "茶叶一主号", "", "测试消息py-00", "")
   pMMsg._Log(msg)
   print(pMMsg._Find_Log("zxcID").Find(msg["msgID"]))

   print()
    