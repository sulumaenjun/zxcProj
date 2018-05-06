﻿# -*- coding: utf-8 -*-
"""
Created on  张斌 2018-01-03 18:00:00 
    @author: zhang bin
    @email:  zhangbin@gsafety.com

    Excel操作 
    @依赖库： xlrd、xlwt
"""
import sys, os, codecs
import xlrd, xlwt 

#加载自定义库
import myEnum, myData, myIO, myData_Trans
  
#定义数据结构枚举
myFiledype = myEnum.enum('string', 'float', 'datetime')

#自定义表结构
class DtTable:
    def __init__(self):     
        self.dataName = ""      #数据集名称 
        self.dataMat = []       #数据集
        self.dataField = []     #数据字段集
        self.dataFieldType = [] #数据字段类型集
        self.sheet = None       #Sheet
        self.sheet_index = 0    #Sheet索引号

        
    #载入文件数据
    def Load(self, strPath, sheet_index = 0, row_start = 1, col_start = 0, all_row = True, field_index = 0):
        #打开文件 
        if (os.path.exists(strPath) == False):
            return False         
        workbook = xlrd.open_workbook(strPath)
        
        # 获取所有sheet
        #print (workbook.sheet_names()) # [u'sheet1', u'sheet2'])
        #sheet2_name = workbook.sheet_names()[0]
        #
        # 获取单元格内容、数据类型
        # print (sheet2.cell(1,0).value.encode('utf-8'))
        # print (sheet2.cell_value(1,0).encode('utf-8'))
        # print (sheet2.row(1)[0].value.encode('utf-8')) 
        # print (sheet2.cell(1,0).ctype)

        # 根据sheet索引或者名称获取sheet内容  sheet2 = workbook.sheet_by_name('sheet2') 
        pSheet = workbook.sheet_by_index(sheet_index)   # sheet索引从0开始
        self.sheet_index = sheet_index
        self.sheet = pSheet

        #提取内容
        pTypes = self.dataFieldType
        nFields = len(pTypes)
        self.dataMat = []
        if(all_row == False): return False
        

        #提取字段信息
        self.dataField = self.loadDt_Row(field_index, col_start)

        #循环提取所有行
        for i in range(row_start, pSheet.nrows):
            pValues = self.loadDt_Row(i, col_start)
            self.dataMat.append(pValues)
        return True

    #载入文件数据行
    def loadDt_Row(self, ind_row, col_start = 0):        
        pTypes = self.dataFieldType
        nFields = len(pTypes)
        pValues = []        
        rows = self.sheet.row_values(ind_row)      # 获取整行内容,列内容: pSheet.col_values(i)
        for j in range(col_start, self.sheet.ncols): 
            if(nFields > j and pTypes[j] == myFiledype.float): 
                pValues.append(float(rows[j]))
                continue
            
            #其他全部为默认类型
            pValues.append(rows[j]) 
        return pValues

    #保存数据
    def Save(self, strDir, fileName, row_start = 0, col_start = 0, cell_overwrite = True, sheet_name = "", row_end = -1, col_end = -1):  
        #创建workbook和sheet对象
        pWorkbook = xlwt.Workbook()  #注意Workbook的开头W要大写
        pName = myData.iif(sheet_name == "","sheet1", sheet_name)
        pSheet = pWorkbook.add_sheet(pName, cell_overwrite_ok = cell_overwrite) 

        #循环向sheet页中写入数据
        nRows = myData.iif(row_end < 0 , len(self.dataMat), row_end)
        nCols = myData.iif(col_end < 0 , len(self.dataMat[0]), col_end)

        #print(nRows, nCols)
        for i in range(row_start, nRows):
            pValues = self.dataMat[i] 
            for j in range(col_start, nCols):
                pSheet.write(i - row_start, j - col_start, str(pValues[j]))                
        #    self.dataMat.append(pValues) 
        #print(self.dataMat)
        
        #保存该excel文件,有同名文件时直接覆盖
        strPath = strDir + "/" + fileName + ".xls"
        strPath.replace("\/", "/")
        strPath.replace("//", "/")
        pWorkbook.save(strPath)
        return True 
    #保存数据
    def Save_csv(self, strDir, fileName, row_start = 0, col_start = 0, sheet_name = "", symbol = ",", row_end = -1, col_end = -1):  
        nRows = myData.iif(row_end < 0 , len(self.dataMat), row_end)
        nCols = myData.iif(col_end < 0 , len(self.dataMat[0]), col_end)
        
        #循环所有格子组装数据
        strLines = ""
        for i in range(row_start, nRows):
            pValues = self.dataMat[i] 
            strLine = str(pValues[col_start])
            for j in range(col_start + 1, nCols):
                strTemp = str(pValues[j])
                if(strTemp.count(",") > 0):   
                    strTemp = "\"" + strTemp + "\""
                elif(strTemp.count('\"') > 0):   
                    strTemp = strTemp.replace("\"","\"\"")
                strLine += symbol + str(strTemp)
            strLines += strLine + "\r\n"

        #保存该csv文件,有同名文件时直接覆盖
        strPath = strDir + "/" + fileName + ".csv"
        myIO.Save_File(strPath, strLines)

        return True 
    #保存数据测试
    def Save_Test(self, strPath, row_start = 0, col_start = 0, cell_overwrite = True, sheet_name = "", row_end = -1, col_end = -1):  
        """
        #-----------使用样式-----------------------------------
        #初始化样式
        style = xlwt.XFStyle()
        #为样式创建字体
        font = xlwt.Font()
        font.name = 'Times New Roman'
        font.bold = True
        #设置样式的字体
        style.font = font
        #使用样式
        sheet.write(0,1,'some bold Times text',style)
        """  
        return True 
    
    #字段索引
    def Get_Index_Field(self, fieldName):
        return self.dataField.index(fieldName);
    def Get_Index_Fields(self, fieldNames):
        inds = {}
        for x in fieldNames:
            inds[x] = self.Get_Index_Field(x)
        return inds;

    #数据长度
    def __len__(self):
        return len(self.dataMat) 
    #数据行
    def __getitem__(self, ind):
        return self.dataMat[ind]
    
    
#载入文件数据(按指定字符分隔)
def loadDataTable(strPath, sheet_index = 0, row_start = 1, col_start = 0, field_index = 0, filetype = []): 
    pDtTable = DtTable() 
    pDtTable.dataFieldType = filetype
    pDtTable.Load(strPath, sheet_index, row_start, col_start, True, field_index)

    #print(pDtTable[0])    
    #pDtTable2 = DtTable()
    #for i in range(0,len(pDtTable[0])):
    #    pValues = []
    #    pValues.append(pDtTable[0][i])
    #    pDtTable2.dataMat.append(pValues)

    #strDir = "F:/Working/张斌/工作文档/程序源码/模型工程化/GModel/src/GModel_Python/GModel_Py_All/GModel_Py_Prj_Department/表格/" 
    #pDtTable2.Save(strDir, "Test3")    
    return pDtTable


def main():
    strPath = "F:/Working/张斌/工作文档/程序源码/模型工程化/GModel/src/GModel_Python/GModel_Py_All/GModel_Py_Prj_Department/表格/Test.xlsx"    
    pTable = loadDataTable(strPath)
     
if __name__ == '__main__':
     exit(main())

