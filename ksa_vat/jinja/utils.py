import json

def string_to_json(json_string):
	return json.loads(json_string)

def has_access(file_url):
	import frappe

	file_exists = frappe.get_all('File',filters={'file_url':file_url},fields=['name'])
	if not file_exists:
		return
	
	file_doc = file_exists[0].name
		
	user = frappe.session.user
	has_access = frappe.has_permission('File', 'read',doc=file_doc, user=user)

	return has_access