import frappe
from frappe import _
from erpnext import get_region
from pyqrcode import create as qr_create
import io
import os
import json

def create_qr_codes(doc,method):
	create_summary_qr_code(doc,method)
	create_detailed_qr_code(doc,method,field='detailed_invoice_qr_code')

def create_detailed_qr_code(doc,method,field):
	print_format = "KSA VAT Format"
	create_qr_code(doc,method,print_format,field)

def create_summary_qr_code(doc,method):
	print_format = "Simplified VAT Invoice"
	create_qr_code(doc,method,print_format)

def create_pos_qr_code(doc,method):
	print_format = "POS Invoice SA"
	create_qr_code(doc,method,print_format)


def create_qr_code(doc, method,print_format=None,qr_field="qr_code"):
	"""Create QR Code after inserting Sales Inv
	"""

	region = get_region(doc.company)
	if region not in ['Saudi Arabia']:
		return

	# if QR Code field not present, do nothing
	if not hasattr(doc, qr_field):
		return

	# Don't create QR Code if it already exists
	qr_code = doc.get(qr_field)
	if qr_code and frappe.db.exists({"doctype": "File", "file_url": qr_code}):
		return

	fields = frappe.get_meta('Sales Invoice').fields
	
	for field in fields:
		if field.fieldname == qr_field and field.fieldtype == 'Attach Image':
			# Creating public url to print format
			default_print_format = frappe.db.get_value('Property Setter', dict(property='default_print_format', doc_type=doc.doctype), "value")
			
			# System Language
			language = frappe.get_system_settings('language')
			
			# creating qr code for the url
			url = f"{ frappe.utils.get_url() }/{ doc.doctype }/{ doc.name }?format={ print_format or default_print_format or 'Standard' }&_lang={ language }&key={ doc.get_signature() }"
			url = url.replace(" ", "%20")
			qr_image = io.BytesIO()
			url = qr_create(url, error='L', encoding='utf-8')
			url.png(qr_image, scale=2, quiet_zone=1)
			
			# making file
			filename = f"QR-CODE-{doc.name}.png".replace(os.path.sep, "__")
			_file = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"content": qr_image.getvalue(),
				"is_private": 1
			})

			_file.save()

			# assigning to document
			doc.db_set(qr_field, _file.file_url)
			doc.notify_update()

			break

		else:
			pass

def delete_qr_code_file(doc, method):
	"""Delete QR Code on deleted sales invoice"""
	
	region = get_region(doc.company)
	if region not in ['Saudi Arabia']:
		return

	qr_code_fields = ['qr_code','detailed_invoice_qr_code']

	for field in qr_code_fields:
		if hasattr(doc, field) and doc.get(field):
			file_doc = frappe.get_list('File', {
				'file_url': doc.get('field'),
				'attached_to_doctype': doc.doctype,
				'attached_to_name': doc.name
			})
			if len(file_doc):
				frappe.delete_doc('File', file_doc[0].name)