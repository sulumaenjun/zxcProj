# -*- coding: utf-8 -*-
"""
Created on  张斌 2019-03-30 15:58:00 
    @author: zhang bin
    @email:  zhangbin@gsafety.com

    pyWeb --股票代码查询
""" 
import sys, os, string, mySystem  

#导入模块
from flask import jsonify, request, flash, render_template, redirect    #导入模块
from flask_wtf import FlaskForm                                         #FlaskForm 为表单基类
from wtforms import BooleanField,IntegerField,DecimalField,StringField,TextAreaField,PasswordField,SubmitField,RadioField,DateField,SelectField,SelectMultipleField       #导入字符串字段，密码字段，提交字段
from wtforms.validators import DataRequired,ValidationError,Email,Regexp,EqualTo,Required,NumberRange,Length

mySystem.Append_Us("", False)  
mySystem.Append_Us("../zxcPy.Robot/Roots", False, __file__)
mySystem.Append_Us("../../zxcPy.Quote/zxcPy.Quotation", False, __file__)
import myIO, myWeb, myWeb_urlLib, myDebug, myData_Json, myRoot_Usr
from myGlobal import gol


# 股票模糊查询页面
class stockQueryForm(FlaskForm):  
    #商品信息
    stockID = StringField('股票代码', [DataRequired(),Length(min=4, max=8)], render_kw={"placeholder": "请输入股票代码"})  
    stockName = StringField('股票名称', [DataRequired(),Length(min=2, max=6)], render_kw={"placeholder": "请输入股票名称"})
 
# 股票行情监测设置页面
class stockQuoteSetForm(FlaskForm):  
    #商品信息
    stockID = StringField('股票代码', [DataRequired(),Length(min=4, max=10)], render_kw={"placeholder": "请输入股票代码"})  
    stockName = StringField('股票名称', [DataRequired(),Length(min=2, max=12)], render_kw={"placeholder": "请输入股票名称/首字母"})
     
    monitorUsrID = StringField('微信账户', [DataRequired()], default="") 
    save = SubmitField('新增监测', render_kw={"class": "form-control","style": "margin-left:10px"})      # 保存按钮
    remove = SubmitField('移除监测')    # 移除按钮

    # Checkbox类型，加上default='checked'即默认是选上的
    monitorRise_Fall = BooleanField('涨跌监测', default='checked',validators=[DataRequired()])
    monitorHourly = BooleanField('整点播报', default='checked',validators=[DataRequired()]) 
    
    exType = StringField('交易所代码', [DataRequired()], render_kw={"style": "display:none;"}) 
    code_id = StringField('股票代码', [DataRequired()],  render_kw={"style": "display:none;"}) 
    code_name = StringField('股票名称', [DataRequired()],  render_kw={"style": "display:none;"}) 

#集中添加所有Web
def add_Webs(pWeb):      
    #添加接口--股票模糊查询 
    @pWeb.app.route('/zxcAPI/robot/stock/query')
    def stockQuery(): 
        #载入配置
        code_id=request.args.get('code_id', "")
        code_name=request.args.get('code_name', "") 

        pStocks = gol._Get_Value('setsStock', None)
        lstStock = pStocks._Find(code_id, code_name)
        
        lstExtypes = []
        lstCode_id = []
        lstCode_Name = []
        lstCode_NameEN = []
        for x in lstStock:
            lstExtypes.append(x.extype)
            lstCode_id.append(x.code_id)
            lstCode_Name.append(x.code_name)
            lstCode_NameEN.append(x.code_name_En)
            
        jsonStocks = myData_Json.Json_Object()
        jsonStocks["extypes"] = lstExtypes
        jsonStocks["code_ids"] = lstCode_id
        jsonStocks["code_names"] = lstCode_Name
        jsonStocks["code_namesEN"] = lstCode_NameEN
        return jsonStocks.ToString() 
    
    #添加页面--股票选择页面-测试
    @pWeb.app.route('/zxcWebs/stock/select', methods = ['GET', 'POST'])    
    def stockSelect():
        form = stockQueryForm()                     #生成form实例，给render_template渲染使用 
        return render_template('stockSelect.html', title = 'Stock Query', form = form)      


    #添加接口--股票设置查询 
    @pWeb.app.route('/zxcWebs/stock/quoteset/query/<usrID>')
    def stockSetQuery(usrID): 
        #strUrl = "http://" + request.remote_addr + ":8669/zxcAPI/robot"    #实际网络地址在阿里云有问题，原因未明
        strUrl = "http://127.0.0.1:8669/zxcAPI/robot"
        strPath = 'stock/QuoteSet/Query?usrID=' + usrID 
             
        #设置查询接口执行
        pWeb = myWeb_urlLib.myWeb(strUrl, bPrint=False)
        strReturn = pWeb.Do_API_get(strPath, "zxcAPI-py")
        print("查询结果：\n", strUrl, "--\n", strReturn, "\n")
        jsonRes = myData_Json.Trans_ToJson(strReturn)

        #结果处理 
        jsonRetrun = myData_Json.Json_Object(jsonRes['text'])
        return jsonRetrun.ToString() 

    #添加页面--股票行情监测设置
    @pWeb.app.route('/zxcWebs/stock/quoteset/<usrID>/<plat>', methods = ['GET', 'POST'])    
    def stockQuoteSet(usrID, plat):
        form = stockQuoteSetForm()                  #生成form实例，给render_template渲染使用  
        if form.validate_on_submit():               #调用form实例里面的validate_on_submit()功能，验证数据是否安全，如是返回True，默认返回False
            #添加订单  
            #strUrl = "http://" + request.remote_addr + ":8669/zxcAPI/robot"
            strUrl = "http://127.0.0.1:8669/zxcAPI/robot"                #实际网络地址在阿里云有问题，原因未明
            if form.save.data:  # 保存按钮被单击 
                editInfo = {}
                
                # 特殊同步
                usrIDs = { usrID : plat}
                #if(usrID == '茶叶一主号' or usrID == '老婆'): 
                #    usrIDs["茶叶一主号"] = plat
                #    usrIDs["老婆"] = plat
                editInfo[form.monitorHourly.label.text] = {'isValid': form.monitorHourly.data, 'msgUsers': usrIDs, 'mark' :""}
                editInfo[form.monitorRise_Fall.label.text] = {'isValid': form.monitorRise_Fall.data, 'msgUsers': usrIDs, 'mark' :""}

                strPath = 'stock/QuoteSet?extype=' + form.exType.data + "&code_id=" + form.code_id.data + "&code_name=" + "&editInfo=" + str(editInfo)  #+ form.code_name.data
            elif form.remove.data:  # 移除按钮被单击
                strPath = 'stock/QuoteSet?extype=' + form.exType.data + "&code_id=" + form.code_id.data + "&code_name=" + "&removeSet=True" + "&usrID=" + usrID 
            
            #修改接口执行
            pWeb = myWeb_urlLib.myWeb(strUrl, bPrint=False)
            strReturn = pWeb.Do_API_get(strPath, "zxcAPI-py")
            jsonRes = myData_Json.Trans_ToJson(strReturn)

            #结果处理 
            return jsonRes['text']
        return render_template('stockQuoteSet.html', title = 'Stock QuoteSet', form = form, usrName_Nick = usrID, usrPlat = plat)

