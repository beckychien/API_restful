import flask_restful

from flask_restful import request
from werkzeug.datastructures import FileStorage
from flask import Flask
from flask_restful import Resource, Api, reqparse
from app.extensions import mongo,mysql2,restapi,cache
import time
import logging
from datetime import date,datetime as dt, timedelta
import codecs, hashlib, os, shutil


app = Flask(__name__)
api = Api(app=app)

@restapi.resource('/data/<string:filename>')
# @restapi.resource('/Data')
class DataApi(Resource):
	def get(self,filename):
		#解析所有fulllog中的log資料
		# print(filename)
		path=os.path.abspath("..")+"processedlog/"
		# for f in os.listdir(path):	
		# fp = open('/fulllog/FOC22361M1Z180928082028.txt', 'r')
		fp = open(path+filename, "r")
		# print(path+f)
		line = fp.readline()
		machine = ''
		sn_code = ''		#儲存機台編號及sn碼
		EndTime = ''
		board = ''
		isAnalogPowered=False
		while line :
			if (line == '}\n' or line == '}}'): line = fp.readline()
			else :
				line = line.strip('{@\n}')
				sp = line.split("|")
				db_sp = [] 	 		#要存入資料庫內的list
				
				while '' in sp: sp.remove('')
				# print (sp)
				#處理要寫入ict_result資料
				if (sp[0] == 'BATCH') :
					db_sp.append(sp[1])
					db_sp.append(sp[7])
					db_sp.append(sp[8])
					logtime = sp[6]
					machine = sp[8]
					board = sp[1]
					line = fp.readline()
					sp = line.split("|")
					while '' in sp: sp.remove('')
					sn_code = sp[1]
					db_sp.append(sp[1])
					db_sp.append(sp[2])
					#日期格式轉換
					Btime = dt.strptime('20'+sp[3], '%Y%m%d%H%M%S')     #BeginTime
					Etime = dt.strptime('20'+sp[9], '%Y%m%d%H%M%S')		#EndTime
					Ltime = dt.strptime('20'+logtime, '%Y%m%d%H%M%S')   #LogTime
					EndTime = Etime
					db_sp.append(Btime)
					db_sp.append(Etime)
					db_sp.append(Ltime)
					print (db_sp)
				#處理各測試結果資料(pre-short、open/short、testjet、analog、poweron、digital、boundary scan、analog powered、frequency、programming)
				elif (sp[0] == 'BLOCK') :
					db_sp.append(sp[1])
					db_sp.append(sp[2])
					# 若sp第一個元素包含(pwr_check)字串則為power_on_result
					if(db_sp[0]=='pwr_check' or db_sp[0]=='pwr_check_pro') : isPowerOn=True
					else : isPowerOn=False 
					line = fp.readline()
					while line :		#block內可能有好幾個不同的測試

						if (line == '}\n'): 
							if (db_sp[0] == 'pwr_check'):     #若讀到pwr_check結尾}則將isAnalogPowered改true,isPowerOn改為false
								isAnalogPowered=True     
								isPowerOn=False
								# print('analog_powered')
							break
							
						else :
							line = line.strip('{@\n}') #移除頭尾@\n
							sp = line.split("{@")
							while '' in sp: sp.remove('')
							lines = []
							for item in sp:
								line = line.strip('{@\n}')
								lines += item.split("|")
							db_sp_new = db_sp + lines
							db_sp_new.insert(0,machine)
							db_sp_new.insert(1,sn_code)
							db_sp_new.append(EndTime)

							if (db_sp_new[4] == 'A-JUM') :
								del db_sp_new[3]		#刪除不必要元素
								del db_sp_new[3]
								print (db_sp_new)
								#WriteDbResult = self.WriteToDb(db_sp_new,1)
							elif (db_sp_new[4] == 'TS'):
								del db_sp_new[3]		#刪除不必要元素
								del db_sp_new[3]
								print (db_sp_new)
								#WriteDbResult = self.WriteToDb(db_sp_new,2)

							elif (db_sp_new[4] == 'A-CAP' or db_sp_new[4] == 'A-RES' or db_sp_new[4] == 'A-MEA' \
							 or db_sp_new[4] == 'A-DIO' or db_sp_new[4] == 'A-NFE' or db_sp_new[4] == 'A-PFE' \
							 or db_sp_new[4] == 'A-NPN' or db_sp_new[4] == 'A-PNP' or db_sp_new[4] == 'A-ZEN'):
								# print(db_sp_new)
								# print('isPowerOn:'+str(isPowerOn))
								# print('isAnalogPowered:'+str(isAnalogPowered))
								# del db_sp_new[3]		#刪除不必要元素
								if (db_sp_new[7]=='LIM2' or db_sp_new[8]=='LIM2') : db_sp_new.insert(9,None) #沒有nominal,需補空值							
								if (len(db_sp_new)<13) : db_sp_new.insert(7,'') #沒有test_condition
								if(isPowerOn and db_sp_new[4] == 'A-MEA'):
									# del db_sp_new[3:5] #analog powered不需要test_type
									del db_sp_new[4]
									# db_sp_new.insert(6,db_sp[0])
									print('============================PowerOn============================')
								elif(isAnalogPowered and db_sp_new[4] == 'A-MEA'):
									del db_sp_new[4] #PowerOn不需要component、test_type
									print('=========================AnalogPowered=========================')
									
								print (db_sp_new)
							line = fp.readline()
				
				elif (sp[0] == 'TJET'):
					db_sp_new = [machine,sn_code,sp[1],sp[3],EndTime,board]
					print (db_sp_new)

					# testjet fail RPT parsing
					if(db_sp_new[2]=='01'):
						line=fp.readline()
						while line:
					
							if (line == '}\n'):break
							else:
								#移除頭尾@\n
								line = line.strip('{@\n}') 
								# split |
								sp = line.split("|")
								db_sp = []
								db_sp = sp[1].split()
								if(sp[0]=='RPT' and len(db_sp)>0) :

									if(db_sp[0]=='Open'):
										#取得第二個元素並移除#字號後取得fail_no
										db_sp_new.append(db_sp[1].replace('#',''))
									elif(db_sp[0]=='Pin'):
										db_sp_new.append(db_sp[1])
									elif(db_sp[0]=='Measured'):
										db_sp_new.append(db_sp[1])
										print(db_sp_new)
										break
									line=fp.readline()
						
										
				elif (sp[0] == 'TS') :
					db_sp_new = [machine,sn_code,sp[1],sp[5],EndTime]
					print (db_sp_new)

					#若測試狀態為失敗,需parsing fail report
					if (sp[1]=='1'):
						line=fp.readline()
						while line:

							if (line == '}\n'): break
				
							else:
								#移除頭尾@\n
								line = line.strip('{@\n}') 

								#split |
								sp = line.split("|")
								db_sp = [] 
								db_sp = sp[1].split()
								test_time=''
								# print(db_sp)
								#陣列第一個元素為RPT且第二個元素用空白切割後陣列長度大於0
								if (sp[0]=='RPT' and len(db_sp)>0):
									
									# 取得fail 時間
									if(db_sp[0]=='Shorts'):
										line=fp.readline().strip('{@\n}')
										str_test_time=(line.split('|'))[1].replace('}','')
										test_time=dt.strptime(str_test_time,'%a %b %d %H:%M:%S %Y')
										
									#陣列第一個元素為Short或Open
									elif (db_sp[0]=='Short' or db_sp[0]=='Open'):
										db_sp_new = [machine,sn_code,EndTime,test_time]
										#取得第fail_type為Short/Open
										db_sp_new.append(db_sp[0])
										#取得第二個元素並移除#字號後取得fail_no
										db_sp_new.append(db_sp[1].replace('#',''))
						 		
									#From為fail point起點 To為fail point終點
									elif(db_sp[0]=='From:' or db_sp[0]=='To:'):
										#若遇到針點為v需取下一行才是針點名稱
										if(db_sp[1]=='v'):
											line=fp.readline()
											point = (line.split())[0].split("|")
											db_sp_new.append(point[1])
										else :
											db_sp_new.append(db_sp[1])
										db_sp_new.append(db_sp[2])

										# ohms
										if(len(db_sp)>3 and db_sp[3]!='Open'):
											db_sp_new.append(db_sp[3])
										else:db_sp_new.append(None)
												
									#讀到Common視為其中一項fail結束
									elif (db_sp[0]=='Common'):print(db_sp_new)
										
									#fail Report結束
									elif ('End' in db_sp[0]):break

									line=fp.readline()

								else : line=fp.readline()	        
				
				# 上電測試-Digital result
				elif (sp[0] == 'D-T') :
					db_sp_new=[]
					db_sp_new.insert(0,machine)
					db_sp_new.insert(1,sn_code)
					if(sp[1]=='1') : db_sp_new.append(sp[5])
					else : db_sp_new.append(sp[4])
					db_sp_new.append(sp[1])
					db_sp_new.append(EndTime)
					print (db_sp_new)
					
				# 上電測試-BoundaryScan result
				elif (sp[0] == 'BS-CON') :
					db_sp_new=[]
					db_sp_new.insert(0,machine)
					db_sp_new.insert(1,sn_code)
					db_sp_new.append(sp[1])
					db_sp_new.append(sp[2])
					db_sp_new.append(EndTime)
					print (db_sp_new)


				line = fp.readline()
		fp.close()
		return {'hello': 'world'}
	"""
	数据接口
	"""
	def __init__(self):
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('file', required=True, type=FileStorage, location='files')

	def post(self,filename):
		#now = time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time()))
		#file = request.files['file']
		path=os.path.abspath("..")+"fulllog/"
		result = {"result":"Fail"}
		WriteDbResult = False
		#read file
		# fp = open('/FCH22307JPY1808301042.txt', 'r')
		# 迴圈讀fulllog檔案中的log做parsing
		try:
			# for f in os.listdir(path):	
			fp = open(path+filename, "r")
			line = fp.readline()
			machine = ''
			sn_code = ''        #儲存機台編號及sn碼
			EndTime = ''
			board = ''
			isAnalogPowered=False
			while line :
				if (line == '}\n' or line == '}}'): line = fp.readline()	#遇到'}'不處理
				else :
					line = line.strip('{@\n}') #去除外圍的括號與＠
					sp = line.split("|")
					db_sp = [] 			#要存入資料庫內的list
					
					#去除空字串
					while '' in sp: sp.remove('')
					if (sp[0] == 'BATCH') :
						db_sp.append(sp[1])
						db_sp.append(sp[7])
						db_sp.append(sp[8])
						logtime = sp[6]
						machine = sp[8]
						board = sp[1]
						line = fp.readline()
						sp = line.split("|")
						while '' in sp: sp.remove('')
						sn_code = sp[1]
						db_sp.append(sp[1])
						db_sp.append(sp[2])
						#日期格式轉換
						Btime = dt.strptime('20'+sp[3], '%Y%m%d%H%M%S')     #BeginTime
						Etime = dt.strptime('20'+sp[9], '%Y%m%d%H%M%S')		#EndTime
						Ltime = dt.strptime('20'+logtime, '%Y%m%d%H%M%S')   #LogTime
						EndTime = Etime
						db_sp.append(Btime)
						db_sp.append(Etime)
						db_sp.append(Ltime)
						self.WriteToDb(db_sp,0)
						#print (db_sp)
					elif (sp[0] == 'BLOCK') :
						db_sp.append(sp[1])
						db_sp.append(sp[2])
						# 若sp第一個元素包含(pwr_check)字串則該block區塊內的A-MEA為power_on_result
						if(db_sp[0]=='pwr_check' or db_sp[0]=='pwr_check_pro') : isPowerOn=True
						else : isPowerOn=False 		
						line = fp.readline()
						while line :		#block內可能有好幾個不同的測試
							if (line == '}\n'): 
								if (db_sp[0] == 'pwr_check'):     #若讀到pwr_check結尾}則將接下來的A-MEA視為AnalogPoweredResult
									isAnalogPowered=True     
									isPowerOn=False
								break			
								
							else :
								line = line.strip('{@\n}')
								sp = line.split("{@")
								while '' in sp: sp.remove('')
								lines = []
								for item in sp:
									line = line.strip('{@\n}')
									lines += item.split("|")
								db_sp_new = db_sp + lines
								
								db_sp_new.insert(0,machine)
								db_sp_new.insert(1,sn_code)
								db_sp_new.append(EndTime)
								#print ('test001')
								#print (db_sp_new)
								if (db_sp_new[4] == 'A-JUM'):
									del db_sp_new[3]		#刪除不必要元素
									del db_sp_new[3]
									WriteDbResult = self.WriteToDb(db_sp_new,1)
									
								elif (db_sp_new[4] == 'A-CAP' or db_sp_new[4] == 'A-RES' or db_sp_new[4] == 'A-MEA' \
									or db_sp_new[4] == 'A-DIO' or db_sp_new[4] == 'A-NFE' or db_sp_new[4] == 'A-PFE' \
						 			or db_sp_new[4] == 'A-NPN' or db_sp_new[4] == 'A-PNP' or db_sp_new[4] == 'A-ZEN'):
									dbType=4
									# del db_sp_new[3]		#刪除不必要元素
									if (db_sp_new[7]=='LIM2' or db_sp_new[8]=='LIM2') : db_sp_new.insert(9,None) #沒有nominal,需補空值							
									if (len(db_sp_new)<13) : db_sp_new.insert(7,'') #沒有test_condition
									if(isPowerOn and db_sp_new[4] == 'A-MEA'):
										del db_sp_new[4]   #PowerOn不需要component、test_type
										dbType=5
									elif(isAnalogPowered and db_sp_new[4] == 'A-MEA'):
										del db_sp_new[4]     #analog powered不需要test_type
										dbType=8


									# del db_sp_new[3:5] #analog powered不需要test_type
									
									WriteDbResult = self.WriteToDb(db_sp_new,dbType)
								
								line = fp.readline()

					# 模擬測試-Testjet
					elif (sp[0] == 'TJET'):
						db_sp_new = [machine,sn_code,sp[1],sp[3],EndTime,board]
						WriteDbResult = self.WriteToDb(db_sp_new,3)

						# testjet fail RPT parsing
						if(db_sp_new[2]=='01'):
							line=fp.readline()
							while line:
						
								if (line == '}\n'):break
								else:
									#移除頭尾@\n
									line = line.strip('{@\n}') 
									# split |
									sp = line.split("|")
									db_sp = []
									db_sp = sp[1].split()
									if(sp[0]=='RPT' and len(db_sp)>0) :

										if(db_sp[0]=='Open'):
											#取得第二個元素並移除#字號後取得fail_no
											db_sp_new.append(db_sp[1].replace('#',''))
										elif(db_sp[0]=='Pin'):
											db_sp_new.append(db_sp[1])
										elif(db_sp[0]=='Measured'):
											db_sp_new.append(db_sp[1])
											WriteDbResult = self.WriteToDb(db_sp_new,31)
											break
										line=fp.readline()
							

					# 模擬測試-open_short
					elif (sp[0] == 'TS') :
						db_sp_new = [machine,sn_code,sp[1],EndTime]
						WriteDbResult = self.WriteToDb(db_sp_new,2)
						#若測試狀態為失敗,需parsing fail report
						if (sp[1]=='1'):
							line=fp.readline()
							while line:
								if (line == '}\n'): break #遇到'}'不處理
				
								else:
									#移除頭尾@\n split |
									line = line.strip('{@\n}') 
									sp = line.split("|") 									
									db_sp = [] 
									db_sp = sp[1].split()
									test_time=''

									#陣列第一個元素為RPT且第二個元素用空白切割後陣列長度大於0
									if (sp[0]=='RPT' and len(db_sp)>0):

										# 取得fail 時間
										if(db_sp[0]=='Shorts'):
											
											line=fp.readline().strip('{@\n}')
											str_test_time=(line.split('|'))[1].replace('}','')
											test_time=dt.strptime(str_test_time,'%a %b %d %H:%M:%S %Y')
											
										
										#陣列第一個元素為Short或Open
										elif (db_sp[0]=='Short' or db_sp[0]=='Open'):
											db_sp_new = [machine,sn_code,EndTime]
											db_sp_new.append(test_time)
											#取得第fail_type為Short/Open
											db_sp_new.append(db_sp[0])
											#取得第二個元素並移除#字號後取得fail_no
											db_sp_new.append(db_sp[1].replace('#',''))

										#From為fail point起點 To為fail point終點
										elif(db_sp[0]=='From:' or db_sp[0]=='To:'):
											#若遇到針點為v需取下一行才是針點名稱
											if(db_sp[1]=="v"):
												line=fp.readline()
												point = (line.split())[0].split("|")
												
												db_sp_new.append(point[1])
											else :
												db_sp_new.append(db_sp[1])
											db_sp_new.append(db_sp[2])

											# ohms
											if(len(db_sp)>3 and db_sp[3]!='Open'):
												db_sp_new.append(db_sp[3])
											else:db_sp_new.append(None)
													
										#讀到Common視為其中一項fail結束
										elif (db_sp[0]=='Common'):
											WriteDbResult = self.WriteToDb(db_sp_new,21)
											
										#fail Report結束
										elif ('End' in db_sp[0]): break

										line=fp.readline()

									else : line=fp.readline()	        
					
					# 上電測試-Digital result
					elif (sp[0] == 'D-T') :
						db_sp_new=[]
						db_sp_new.insert(0,machine)
						db_sp_new.insert(1,sn_code)
						if(sp[1]=='1') : db_sp_new.append(sp[5])
						else : db_sp_new.append(sp[4])
						db_sp_new.append(sp[1])
						db_sp_new.append(EndTime)
						WriteDbResult = self.WriteToDb(db_sp_new,6)
					
					# 上電測試-BoundaryScan result
					elif (sp[0] == 'BS-CON') :
						db_sp_new=[]
						db_sp_new.insert(0,machine)
						db_sp_new.insert(1,sn_code)
						db_sp_new.append(sp[1])
						db_sp_new.append(sp[2])
						db_sp_new.append(EndTime)
						WriteDbResult = self.WriteToDb(db_sp_new,7)

					line = fp.readline()

				#WriteDbResult = self.WriteToDb(sp)
		###################### 		
			
				# print(file.name, file.mimetype, file.stream)
				#file.save('./data/'+now+r'.csv')
			fp.close()
			#移動處理完的檔案到上一層的processedlog資料夾中
			shutil.move(path+filename,os.path.abspath("..")+"processedlog/")

		except Exception as err:
			# print(filename)
			print("[error]: {0}".format(err))
		
		if WriteDbResult :
			result['result'] = 'Success'
		return result

	def WriteToDb(self,lists,type):
		#type 0:  log檔基本資訊
		#type 1:  jumper測試
		#type 2:  short測試
		#type 21: short fail RPT
		#type 3:  testjet
		#type 31: testjet fail RPT
		#type 4:  analog
		#type 5:  power on 
		#type 6:  digital
		#type 7:  boundary scan
		#type 8: analog_powered
		if (type == 0) :
			Items = 'insert ignore into ICT_Project.ict_result(board,operator,machine,sn,status,start_time,end_time,log_time) values ('
		elif (type == 1) :
			Items = 'insert ignore into ICT_Project.preshort_result(machine,sn,component,status,measured,test_type,high_limit,low_limit,end_time) values ('
		elif (type == 2) :
			Items = 'insert ignore into ICT_Project.open_short_result(machine,sn,status,end_time) values ('
		elif (type == 21) :
			Items = 'insert ignore into ICT_Project.open_short_fail(machine,sn,end_time,test_time,fail_type,fail_no,from_point,from_BRC,from_ohms,end_point,end_BRC,end_ohms) values ('
		elif (type == 3) :
			Items = 'insert ignore into ICT_Project.testjet_result(machine,sn,status,device,end_time,board) values ('
		elif (type == 31) :
			Items = 'insert ignore into ICT_Project.testjet_fail(machine,sn,status,device,end_time,board,fail_no,pins,measured) values ('		
		elif (type == 4) :
			Items = 'insert ignore into ICT_Project.analog_result(machine,sn,component,block_status,test_type,status,measured,test_condition,limit_type,nominal,high_limit,low_limit,end_time) values ('
		elif (type == 5) :
			Items = 'insert ignore into ICT_Project.power_on_result(machine,sn,power_check_type,block_status,status,measured,power_check,limit_type,nominal,high_limit,low_limit,end_time) values ('				
		elif (type == 6) :
			Items = 'insert ignore into ICT_Project.digital_result(machine,sn,component,status,end_time) values ('
		elif (type == 7) :
			Items = 'insert ignore into ICT_Project.boundary_scan_result(machine,sn,component,status,end_time) values ('
		elif (type == 8) :
			Items = 'insert ignore into ICT_Project.analog_powered_result(machine,sn,component,block_status,status,measured,test_condition,limit_type,nominal,high_limit,low_limit,end_time) values ('
		
		
		for item in lists:
			if str(item)=="None":Items=Items+'null'+','
			else : Items = Items + '"' + str(item) + '"' + ','
		Items = Items.strip(',')
		Items += ')'
		print (Items)
		try :
			conn = mysql2.connect()
			cursor = conn.cursor()
			#print (Items)
			cursor.execute(Items)
			conn.commit()
			cursor.close()
			conn.close()
			return True	
		except Exception as inst:
			print('FulearnV4 Test Data MySql Write Err'+' type-'+str(type))
			logging.getLogger('error_Logger').error('FulearnV4 Test Data MySql Write Err'+' type-'+str(type))
			logging.getLogger('error_Logger').error(inst)
			with codecs.open('./Log/ErrPost/Test_{0}.sql'.format(dt.now().strftime('%Y%m%d%H%M%S')),'wb', "utf-8") as ErrOut :
				ErrOut.write(Items)
				ErrOut.write('\n')
				ErrOut.close()
		return False


		
api.add_resource(DataApi, '/data/')


if __name__ == '__main__':
	app.run(debug=True)