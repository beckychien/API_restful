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

@restapi.resource('/Fixture/<string:filename>')
# @restapi.resource('/Wirelist')
class Fixture(Resource):
	def get(self,filename):
		
		path=os.path.abspath("..")+"fixture/"

		fp = open(path+filename, 'r')

		line = fp.readline()
		
		board = ''
		probes = ''
		x=''
		y=''
		status=''
		isNode=False
		count=0
		while line :

			sp=line.split()
			# print(sp)
			
			if (len(sp) > 0 and sp[0] == 'END'): break
			elif (len(sp) > 0 and sp[0] == 'BOARD') : board=sp[1].replace('"','') 
			elif (len(sp) > 0 and (sp[0] == 'NODE')):

				node=sp[1].replace('"','')
				pins=[]
				probes_dict={}
				wire_pins=[]
				wire_probes=[]
				# print(node)
				line=fp.readline()				
				while line:
					sp=line.split()
					# print(sp)
					if(len(sp)>0 and sp[0] == 'PINS'):
						# print(node)
						line=fp.readline()
						inNode=True
			
						while inNode:
					
							sp = line.replace(';','').split()
							if(sp[0].isdigit()):								
								pins.append(sp[0].strip())
								# print(sp[0])
								line=fp.readline()
									# print(line)				
							elif(sp[0]=='PROBES'):
								# print(pins)
								line=fp.readline()
								while inNode:
									sp=line.split()
									# wires_dict
									if(len(sp)>0 and sp[0]=='WIRES'):
									
										line=fp.readline()
										
										while line:
											sp=line.split()
											if(len(sp)>1):		

												wire_pins.append(sp[0].strip())
												wire_probes.append(sp[2].strip())

												line=fp.readline()

											# NODE結束
											else:
												inNode=False

												# 從pins找座標
												for x in range(len(wire_pins)):
													# node=''
													pin=wire_pins[x]
													probe=wire_probes[x]
													db_sp=[]
													while len(db_sp)==0:
								
														if(probe in probes_dict):
															probe_sp=probes_dict[probe].split()
															x=probe_sp[0]
															y=probe_sp[1]
															status=''
															if(len(probe_sp)>2):
																for p in range(2,len(probe_sp)):
																	status+=probe_sp[p]+' '

															db_sp=[board,node,pin,probe,x,y,status.strip()]
														
															print(db_sp)
										
	
														else:
															new_pin=probe

															for y in range(len(wire_pins)):
																if new_pin==wire_pins[y]:
																	probe=wire_probes[y]
																elif (pin==wire_pins[y] and y!=x):
																	probe=wire_probes[y]

												# 從probes找座標
												for px in range(len(wire_probes)):
													if(wire_probes[px][0:1]!='P'):	
														# node=''
														pin=wire_probes[px]
														new_pin=wire_pins[px]
														# probe=wire_probes[px]
														db_sp=[]
														for py in range(len(wire_pins)):
															if(new_pin==wire_pins[py] and px!=py):
																probe=wire_probes[py]
																
															elif(pin==wire_pins[py]):
																probe=wire_probes[py]
																# print(probe)
														while len(db_sp)==0:
									
															if(probe in probes_dict):
																probe_sp=probes_dict[probe].split()
																x=probe_sp[0]
																y=probe_sp[1]
																status=''
																if(len(probe_sp)>2):
																	for p in range(2,len(probe_sp)):
																		status+=probe_sp[p]+' '

																db_sp=[board,node,pin,probe,x,y,status.strip()]
															
																print(db_sp)
											
		
															else:
																new_pin=probe
																for y in range(len(wire_pins)):
																	if new_pin==wire_pins[y]:
																		probe=wire_probes[y]
																		break
																	elif (pin==wire_pins[y] and y!=x):
																		probe=wire_probes[y]
												break

									# probes_dict
									else:
										sp=line.replace(';','').split()
										value=''
										if(len(sp)>2):
											for index in range(1,len(sp)):
												value+=sp[index].replace(',','')+' '
											probes_dict[sp[0]]=value
										line=fp.readline()

					else:break


	
			line=fp.readline()
			# print(line)
		
		fp.close()
		print(count)
		return {'hello': 'world'}
	"""
	数据接口
	"""
	def __init__(self):
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('file', required=True, type=FileStorage, location='files')

	def post(self,filename):
		result = {"result":"Fail"}
		WriteDbResult = False
		
		try:
			path=os.path.abspath("..")+"fixture/"

			fp = open(path+filename, 'r')

			line = fp.readline()
			
			board = ''
			probes = ''
			x=''
			y=''
			status=''
			isNode=False
			count=0
			while line :

				sp=line.split()
				# print(sp)
				
				if (len(sp) > 0 and sp[0] == 'END'): break
				elif (len(sp) > 0 and sp[0] == 'BOARD') : board=sp[1].replace('"','') 
				elif (len(sp) > 0 and (sp[0] == 'NODE')):

					node=sp[1].replace('"','')
					pins=[]
					probes_dict={}
					wire_pins=[]
					wire_probes=[]
			
					line=fp.readline()				
					while line:
						sp=line.split()
					
						if(len(sp)>0 and sp[0] == 'PINS'):
			
							line=fp.readline()
							inNode=True
							
							while inNode:
						
								sp = line.replace(';','').split()
								if(sp[0].isdigit()):								
									pins.append(sp[0].strip())
							
									line=fp.readline()
												
								elif(sp[0]=='PROBES'):
							
									line=fp.readline()
									while inNode:
										sp=line.split()
										# wires_dict
										if(len(sp)>0 and sp[0]=='WIRES'):
										
											line=fp.readline()
											
											while line:
												sp=line.split()
												if(len(sp)>1):		

													wire_pins.append(sp[0].strip())
													wire_probes.append(sp[2].strip())

													line=fp.readline()

												# NODE結束
												else:
													inNode=False
													# 從pins找座標
													for x in range(len(wire_pins)):
														# node=''
														pin=wire_pins[x]
														probe=wire_probes[x]
														db_sp=[]
														while len(db_sp)==0:
									
															if(probe in probes_dict):
																probe_sp=probes_dict[probe].split()
																x=probe_sp[0]
																y=probe_sp[1]
																status=''
																if(len(probe_sp)>2):
																	for p in range(2,len(probe_sp)):
																		status+=probe_sp[p]+' '

																db_sp=[board,node,pin,probe,x,y,status.strip()]
															
																WriteDbResult = self.WriteToDb(db_sp,0)
											
		
															else:
																new_pin=probe

																for y in range(len(wire_pins)):
																	if new_pin==wire_pins[y]:
																		probe=wire_probes[y]
																	elif (pin==wire_pins[y] and y!=x):
																		probe=wire_probes[y]

													# 從probes找座標
													for px in range(len(wire_probes)):
														if(wire_probes[px][0:1]!='P'):	
													
															pin=wire_probes[px]
															new_pin=wire_pins[px]
														
															db_sp=[]
															for py in range(len(wire_pins)):
																if(new_pin==wire_pins[py] and px!=py):
																	probe=wire_probes[py]
																	
																elif(pin==wire_pins[py]):
																	probe=wire_probes[py]
						
															while len(db_sp)==0:
																if(probe in probes_dict):
																	probe_sp=probes_dict[probe].split()
																	x=probe_sp[0]
																	y=probe_sp[1]
																	status=''
																	if(len(probe_sp)>2):
																		for p in range(2,len(probe_sp)):
																			status+=probe_sp[p]+' '

																	db_sp=[board,node,pin,probe,x,y,status.strip()]
																
																	WriteDbResult = self.WriteToDb(db_sp,0)
												
																else:
																	new_pin=probe
																	for y in range(len(wire_pins)):
																		if new_pin==wire_pins[y]:
																			probe=wire_probes[y]
																			break
																		elif (pin==wire_pins[y] and y!=x):
																			probe=wire_probes[y]																		
																	
													break

										# probes_dict
										else:
											sp=line.replace(';','').split()
											value=''
											if(len(sp)>2):
												for index in range(1,len(sp)):
													value+=sp[index].replace(',','')+' '
												probes_dict[sp[0]]=value
											line=fp.readline()

						else:break

				line=fp.readline()
		
		
			fp.close()

		except Exception as err:
			# print(filename)
			print("[error]: {0}".format(err))
		
		if WriteDbResult :
			result['result'] = 'Success'
		return result

	def WriteToDb(self,lists,type):
		#type 0:  log檔基本資訊
		if (type == 0) :
			Items = 'insert ignore into ICT_Project.fixture(board,node,pins,probes,x,y,status) values ('
		
		
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
			print('ICT Test Data MySql Write Err'+' type-'+str(type))
			logging.getLogger('error_Logger').error('ICT Test Data MySql Write Err'+' type-'+str(type))
			logging.getLogger('error_Logger').error(inst)
			with codecs.open('./Log/ErrPost/Test_{0}.sql'.format(dt.now().strftime('%Y%m%d%H%M%S')),'wb', "utf-8") as ErrOut :
				ErrOut.write(Items)
				ErrOut.write('\n')
				ErrOut.close()
		return False


		
api.add_resource(Fixture, '/fixture/')


if __name__ == '__main__':
	app.run(debug=True)