# -*- coding: utf-8 -*-

import xmlrpclib
import info

def blog_post(blogApiId, blogId, blogPw, blogApiUrl, title, contents, publish, category, blogtype):
	server = xmlrpclib.ServerProxy(blogApiUrl, encoding='utf-8', allow_none=True)

	contents = contents.replace("&apos;", "\'")		# 따옴표가 &apos 로 표기되는 것을 방지함.

	if blogtype <> 3:	# 3번은 네이버블로그임.
		blogContents = {'title':title, 'description':contents, 'categories':[category]}
	else:
		blogContents = {'title':title, 'description':contents}

	post_id = server.metaWeblog.newPost(blogApiId, blogId, blogPw, blogContents, publish)

	return post_id

if __name__ == '__main__':

	# 테스트용 블로그 정보
	blogApiId = ''
	blogId = ''
	blogPw = ''
	apiUrl = ''

	resultPostid = blog_post(blogApiId, blogId, blogPw, apiUrl, 'T2B TEST', 'TEST', True, '', 'naverblog')
	print resultPostid