# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------
# 수동으로 실행하고 싶은 경우 아래와 같이 DB의 t2b_delivery_list 의 idx와 날짜를 지정하면 됨
# t2b.py 94 2011-08-30
#
# 인자를 지정하지 않으면 현재 시간 기준으로 실행 됨.
# 이 프로그램은 shell에서 매일 밤 12시 5분에 자동 실행되도록 아래와 같이 cron 설정 되어 있음.
# 5 0 * * * python /var/www/t2b_engine/t2b.py
#-------------------------------------------------------------------

#-------------------------------------------------------------------
# 제작 정보
# 최초 개발일 : 2009년 7월 26일
# 2차 재 개발일 : 2010년 11월 21일
# 제작자 : 박주명 (sadrove@gmail.com)
# 제작자 홈페이지 : http://www.sadrove.com
# 본 프로그램은 이 제작 정보를 수정없이 표시하는 조건하에서 누구나 자유롭게 수정하여 배포할 수 있습니다.
#-------------------------------------------------------------------

import info		# T2B 기본 정보
import blogpost	# 블로그로 포스팅
import MySQLdb
import urllib2
import feedparser
import time
import datetime
import pprint
import traceback
import os
import re
import sys

# DB 커서 생성
t2bDb = MySQLdb.connect(user=info.dbUser, passwd=info.dbPasswd, db=info.dbInfo)
cursordeliveryData = t2bDb.cursor(MySQLdb.cursors.DictCursor)

today = time.localtime()		# 현재 날짜
today = time.localtime(time.mktime(today) - (9 * 60 * 60))

# t2b.py 실행시 인자를 지정하여 수동 글배달 할 수 있음.
if len(sys.argv) is 1:			# 인자가 없을 경우
	directMemberIdx = ''
	directDate = ''
	# 가져올 트윗 날짜(현재 시간의 12시간 전으로 설정함. T2B가 돌아가는 시간은 0시~6시이므로 넉넉하게)
	getDay = time.strftime('%Y-%m-%d', time.localtime(time.mktime(today) - (12 * 60 * 60)))
else:							# 인자가 있을 경우
	directMemberIdx = sys.argv[1]
	directDate = sys.argv[2]
	getDay = directDate

# 가져오려는 날짜(getDay)를 기준으로 어제/다음날 날짜를 자동 지정함.
transGetDay = datetime.date(int(getDay[:4]), int(getDay[5:7]), int(getDay[8:10]))
sDay = transGetDay + datetime.timedelta(-1)
lDay = transGetDay + datetime.timedelta(1)
titleDay = '%s년 %s월 %s일' % (getDay[:4], getDay[5:7], getDay[8:10])		# 타이틀 날짜를 강제로 지정함.

tagStrip = re.compile(r'<[^>]*>')	# HTML 태그 제거

print sDay, getDay, lDay

#------------------------------------------------------------------------------

# 해당 아이디의 트윗을 검색해서 읽어들임
def get_atom(twiId, sDay, lDay):
	url = "http://search.twitter.com/search.atom?from=%s&since=%s&until=%s&rpp=100" % (twiId, sDay, lDay)

	result = urllib2.urlopen(url).read()

	return result

# 보낼 트위터를 받아서 HTML로 랩핑
def get_html(twiList, postType):
	html = ''
	# postType 이 1일 경우
	if postType == 1:
		html += "<ul style='width:90% ; padding:0 10px 0 10px; list-style: none;'>"

		for data in twiList:
			data[1] = time.localtime(time.mktime(data[1]) + (9 * 60 * 60))
			html += "<li style='border-bottom:1px dashed #DDD; padding:7px 0 5px 0; list-style: none;'>%s %s-%s %s:%s <a href='%s' target='_blank' style='font-size:8pt; color:#646464;'>#</a></li>" % (data[0], data[1].tm_mon, data[1].tm_mday, data[1].tm_hour, data[1].tm_min, data[2])
		html += "</ul>"

	# postType 이 2일 경우
	elif postType == 2:
		html += "<ul style='width:90% ; padding:10px 0 0 10px; list-style: none;'>"
		for data in twiList:
			data[1] = time.localtime(time.mktime(data[1]) + (9 * 60 * 60))
			html += "<li style='padding:7px 0 5px 0; list-style: none;'>%s %s-%s %s:%s <a href='%s' target='_blank' style='font-size:8pt; color:#646464;'>#</a></li>" % (data[0], data[1].tm_mon, data[1].tm_mday, data[1].tm_hour, data[1].tm_min, data[2])
		html += "</ul>"

	html += "<div style='width:95%;text-align:right;padding:5px 0 0 0;'><a href='http://t2b.kr' target='_blank' style='color:#595454;font-size:8pt;text-decoration:none;float:right;'>t2b.kr</a></div>"

	return html

# 글배달 해야할 목록을 DB에서 가져옴.
def get_delivery_list():
	#selQry = "SELECT * FROM t2b_delivery_list ORDER BY idx DESC;"
	#selQry = "SELECT * FROM t2b_delivery_list WHERE idx=485;" # 테스트 주소임.
	if directMemberIdx != '':
		selQry = "SELECT * FROM t2b_delivery_list WHERE member_idx=%s;" % (directMemberIdx) # 테스트 주소임 - 트위터 아이디는 sadrove는 94
		print selQry
	else:
		selQry = "SELECT * FROM t2b_delivery_list ORDER BY idx DESC;"

	cursordeliveryData.execute(selQry)
	recs= cursordeliveryData.fetchall()
	dl = [list([x]) for x in recs]	# 글배달할 목록을 DB에서 가져와 리스트로 저장

	return dl


def t2bRun():
	nowtime = time.strftime("%Y-%m-%d %H:%M:%S")

	if os.path.isfile('/var/www/t2b_engine/log/t2b_history.log'):
		f = open('/var/www/t2b_engine/log/t2b_history.log', 'a')
	else:
		msg = "log Start : %s \n" % nowtime
		f = open('/var/www/t2b_engine/log/t2b_history.log', 'a')
		f.write(msg)

	DeliveryList = get_delivery_list()		# 글배달 할 목록을 가져옴

	# 각 목록을 돌면서 트윗을 가져온 후 블로그로 보냄
	for dl in DeliveryList:

		try:
			getTwit = get_atom(dl[0]['twi_id'], sDay, lDay)		# 해당 아이디의 트윗을 가져옴
			getContent = feedparser.parse(getTwit)				# 가져온 트윗(Atom)을 파싱함
			
		except:
			logmsg = '[TWI_ID BLANK ERROR] [%s] Delivery_list IDX : %s\n' % (nowtime, dl[0]['idx']) # DB에 트위터 아이디가 null일 경우 기록함.
			f.writelines(logmsg)
			traceback.print_exc(file=open('/var/www/t2b_engine/log/t2b_history.log','a'))
		#pprint.pprint(getContent)
		# 엔트리를 돌면서 내용/링크/날짜를 가져옴.
		twiList = []
		i = 0
		tweetCnt = 0

		blogTitle = "@%s의 트위터 : %s" % (dl[0]['twi_id'], titleDay)
		mentionRemove = dl[0]['mention']		# 0은 멘션 포함, 1은 멘션 제거
		try:
			while '' != getContent.entries[i].content[0].value:
				# 이 트윗의 날짜를 뽑아냄. ex) 2011-11-23
				thisDay = time.strftime('%Y-%m-%d', time.localtime(time.mktime(getContent.entries[i].published_parsed) + (9 * 60 * 60)))
				twiContent = getContent.entries[i].content[0].value
				twiContent = tagStrip.sub('', twiContent)
				
				# 트위터 트윗 출력하기
				#print twiContent
				#print 'thisDay = %s | getDay = %s\n' % (thisDay, getDay)
				
				if(thisDay == getDay):	# 어제 날짜인 트윗만 모음
					# 멘션 포함
					if mentionRemove == 0:
						list_group = []
						list_group.append(getContent.entries[i].content[0].value)
						list_group.append(getContent.entries[i].published_parsed)
						list_group.append(getContent.entries[i].link)
						twiList.append(list_group)
						tweetCnt += 1
					# 멘션 제거
					else:
						if twiContent[0] != '@':
							list_group = []
							list_group.append(getContent.entries[i].content[0].value)
							list_group.append(getContent.entries[i].published_parsed)
							list_group.append(getContent.entries[i].link)
							twiList.append(list_group)
							tweetCnt += 1
						else:
							pass
				i += 1
		except:
			pass

		if tweetCnt > 0:	# 트윗이 있을 경우에만 블로그로 보냄
			# 블로그로 포스팅 함
			try:
				# 티스토리를 제외한 블로그들은 blog pw를 api key로 대체
				if dl[0]['blog_pw'] == '': blog_pw = dl[0]['blog_apikey']
				else: blog_pw = dl[0]['blog_pw']

				# 블로그가 티스토리나 이글루스의 경우 카테고리 지정
				if dl[0]['blog_type'] == 1 or dl[0]['blog_type'] == 2:
					resultPostId = blogpost.blog_post(dl[0]['blog_apikey'], dl[0]['blog_id'], blog_pw, dl[0]['blog_apiurl'], blogTitle, get_html(twiList, dl[0]['post_type']), True, dl[0]['category'], dl[0]['blog_type'])
				else:
					resultPostId = blogpost.blog_post(dl[0]['blog_apikey'], dl[0]['blog_id'], blog_pw, dl[0]['blog_apiurl'], blogTitle, get_html(twiList, dl[0]['post_type']), True, '', dl[0]['blog_type'])

				# 글배달 횟수 기록
				updateQry = "UPDATE t2b_member SET delivery_cnt = delivery_cnt + 1 WHERE idx = %s" % dl[0]['member_idx']
				cursordeliveryData.execute(updateQry)

				# 글배달 마지막 성공일 기록
				updateQry = "UPDATE t2b_delivery_list SET last_update = '%s' WHERE idx = %s" % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(today) - (12 * 60 * 60))), dl[0]['idx'])
				cursordeliveryData.execute(updateQry)

				time.sleep(3)		# 블로그 서비스에서 스팸 인식 방지를 위해 잠시 멈춤
				print "Done : %s" % (dl[0]['idx'])

				logmsg = '[Done] [%s] Delivery_list IDX : %s\n' % (nowtime, dl[0]['idx'])
				f.writelines(logmsg)
				traceback.print_exc(file=open('/var/www/t2b_engine/log/t2b_history.log','a'))

			except:
				logmsg = '[ERROR] [%s] Delivery_list IDX : %s\n' % (nowtime, dl[0]['idx'])
				f.writelines(logmsg)
				traceback.print_exc(file=open('/var/www/t2b_engine/log/t2b_history.log','a'))
		else:
			pass
if __name__ == '__main__':
	t2bRun()
