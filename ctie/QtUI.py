import os
import sys
from PySide import QtCore, QtGui, QtUiTools
from helpers import *
from ctie import *
from qt import *

class Clicked(QtCore.QObject):
	def __init__(self, action):
		action.triggered.connect(self.triggered)

	def triggered(self):
		pass

# http://www.noobslab.com/2014/03/give-new-looks-to-gimp-image-editor.html

clear_tempdir = True

class CtieUI(object):
	def __init__(self):
		self.ctie = Ctie(self)
		self.signal_mask = False
		self.focus_field = (None, None)
		self.focus_entry = None
		self.preview_canvas = None
		self.canvas = None
		self.zoom = 100
		self.selstart = (None, None)
		self.selend = (None, None)
		self.mode = None

		uiFile = "ctie.ui"
		for datadir in [os.path.dirname(__file__),'/usr/local/share/ctie']:
			fullpath = os.path.join(datadir, uiFile)
			if os.path.exists(fullpath):
				break
		else:
			sys.stderr.write('Unable to find {0}\n'.format(uiFile))
			sys.exit(1)

		app = QtGui.QApplication(sys.argv)
		loader = QtUiTools.QUiLoader()
		ui = loader.load(os.path.join(os.path.dirname(__file__), uiFile), None)
		ui.show()

		#toolbar
		self.uiToolBar = Toolbar(self, ui.findChild(QtGui.QToolBar, "toolBar"))
		self.uiItemList = ItemList(self, ui.findChild(QtGui.QVBoxLayout, "itemList"), ui.findChild(QtGui.QScrollArea, "itemListScroller"))
		self.uiStatusBar = ui.findChild(QtGui.QStatusBar, "statusBar")

		sys.exit(app.exec_())


	def set_status(self, s):
		self.uiStatusBar.showMessage(s)

	def edit_regex(self, *arg):
		self.builder.get_object("regex").get_buffer().set_text(self.ctie.getRegex())
		self.builder.get_object("regex_window").show()

	def regex_apply(self, *arg):
		b = self.builder.get_object("regex").get_buffer()
		text = b.get_text(b.get_start_iter(), b.get_end_iter(), 0).strip()
		try:
			text = text.decode("utf-8")
		except:
			pass
		self.ctie.setRegex(text)
		self.builder.get_object("regex_window").hide()

	def selectPreviousItem(self, *arg):
		item = self.ctie.getCurrentItem()
		if item is None:
			return
		self.ctie.selectPrevItem()

	def selectNextItem(self, *arg):
		item = self.ctie.getCurrentItem()
		if item is None:
			return
		self.ctie.selectNextItem()

	def key_press(self, obj, evt):
		collation_mode = self.toggle_collation.get_active()
		if evt.keyval==Gdk.KEY_Page_Down:
			if not collation_mode or evt.state & Gdk.ModifierType.CONTROL_MASK:
				self.selectNextItem()
			else:
				self.ctie.selectNextChild()
		elif evt.keyval==Gdk.KEY_Page_Up:
			if not collation_mode or evt.state & Gdk.ModifierType.CONTROL_MASK:
				self.selectPreviousItem()
			else:
				self.ctie.selectPrevChild()
		elif evt.keyval==Gdk.KEY_Delete and self.canvas.has_focus():
			self.delete()
		elif (evt.keyval==Gdk.KEY_A or evt.keyval==Gdk.KEY_a) and evt.state & Gdk.ModifierType.CONTROL_MASK and self.canvas.has_focus():
			self.ctie.deselectAllChildren()
			if not evt.state & Gdk.ModifierType.SHIFT_MASK:
				self.ctie.selectAllChildren()
		elif (evt.keyval==Gdk.KEY_C or evt.keyval==Gdk.KEY_c) and evt.state & Gdk.ModifierType.CONTROL_MASK and self.canvas.has_focus():
			self.copy()
		elif (evt.keyval==Gdk.KEY_V or evt.keyval==Gdk.KEY_v) and evt.state & Gdk.ModifierType.CONTROL_MASK and self.canvas.has_focus():
			self.paste()

	def ltrim(self, *arg):
		self.ctie.leftTopTrim();

	def rtrim(self, *arg):
		self.ctie.rightBottomTrim();

	def set_value(self, *arg):
		self.builder.get_object('set_value_window').show()

	def set_value_apply(self, *arg):
		key = self.builder.get_object('set_value_key').get_text()
		value = self.builder.get_object('set_value_value').get_text()
		isFormula = self.builder.get_object('set_value_value_is_formula').get_active()
		if not key:
			return
		self.ctie.batchSetTag(key, value, isFormula)

	def open_project(self, *arg):
		global tempdir, clear_tempdir
		filec = Gtk.FileChooserDialog("Open", self.builder.get_object("main_window"), Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
		if Gtk.Dialog.run(filec)==Gtk.ResponseType.ACCEPT:
			filename = filec.get_filename()
			filec.destroy()
			if self.ctie.load(filename):
				clear_tempdir = False
			else:
				self.set_status('Failed loading %s' % filename)
				return
		else:
			filec.destroy()
			return

	def save_project(self, *arg):
		global clear_tempdir
		if not self.ctie.clips:
			return
		filec = Gtk.FileChooserDialog("Save", self.builder.get_object("main_window"), Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
		if Gtk.Dialog.run(filec)==Gtk.ResponseType.ACCEPT:
			self.ctie.save(filec.get_filename())
			clear_tempdir = False
		filec.destroy()

	def copy_setting(self, obj, *arg):
		tagsbox = self.builder.get_object("copy_setting_tags")
		c = tagsbox.get_child()
		if c:
			tagsbox.remove(c)
		tags_table = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
		tagsbox.add(tags_table)
		for i,key in enumerate(self.ctie.tags):
			toggle = Gtk.CheckButton.new_with_label(key)
			if key in self.ctie.copy_tags:
				toggle.set_active(True)
			else:
				toggle.set_active(False)
			toggle.connect('toggled', self.copy_setting_toggle, key)
			tags_table.pack_start(toggle,False,False,0)
		self.builder.get_object("copy_setting_window").show_all()

	def copy_setting_toggle(self, obj, key):
		if obj.get_active():
			self.ctie.enableCopyTag(key)
		else:
			self.ctie.disableCopyTag(key)

	def copy(self, *arg):
		if not self.ctie.selections:
			self.set_status('Nothing to copy, select something!')
		self.ctie.copy()

	def paste(self, *arg):
		self.ctie.paste()
		self.canvas.queue_draw()

	def autopaste(self, *arg):
		self.ctie.autoPaste()
		self.canvas.queue_draw()

	def delete(self, *arg):
		self.ctie.deleteSelectedChildren()

	def do_export(self, *arg):
		outputdir = self.builder.get_object('output_dir').get_filename()
		export_filter = CQL(self.builder.get_object('export_filter').get_text())
		if not export_filter:
			print "Invalid filter"
			return
		export_content = CQL(self.builder.get_object('export_content').get_text())
		if not export_content:
			print "Invalid content"
			return
		export_path = CQL(self.builder.get_object('path_pattern').get_text())
		if not export_path:
			print "Invalid path"
			return
		self.ctie.export(export_filter, export_content, export_path, outputdir)

	def append_tag(self, *arg):
		b = self.builder.get_object('path_pattern')
		b.set_text("%s${%s}" % (b.get_text(), self.builder.get_object('tags_list').get_active_text()))

	def export_show(self, *arg):
		self.builder.get_object('export_window').show()

	def add_tag(self, *arg):
		tag = self.builder.get_object('new_tag').get_text()
		if not tag:
			return
		r = self.ctie.addTag(tag)
		if not r:
			self.set_status("Tag %s already exists" % tag)

	def canvas_draw(self, widget, cr):
		item = self.ctie.getCurrentItem()
		if item is None:
			return
		factor = self.zoom*0.01
		width = item.x2-item.x1
		height = item.y2-item.y1

		self.canvas.set_size_request(int(width*factor), int(height*factor))
		self.canvas.set_halign(Gtk.Align.CENTER)
		self.canvas.set_valign(Gtk.Align.CENTER)

		item.draw(self.canvas, cr, factor)

		cr.scale(factor, factor)
		sx1, sy1 = self.selstart
		sx, sy = self.selend
		if sx1>sx:
			sx1,sx = sx,sx1
		if sy1>sy:
			sy1,sy = sy,sy1
		if self.selstart!=(None, None) and self.selend!=(None, None):
			xoff = self.selend[0]-self.selstart[0]
			yoff = self.selend[1]-self.selstart[1]
		else:
			xoff = 0
			yoff = 0

		if self.toggle_horizontal_splitter.get_active() and self.selend[0]:
			cr.set_source_rgba(0,255,0,255)
			cr.move_to(self.selend[0],float(0))
			cr.line_to(self.selend[0],float(item.y2-item.y1))
			cr.stroke()
			return
		if self.toggle_vertical_splitter.get_active() and self.selend[0]:
			cr.set_source_rgba(0,255,0,255)
			cr.move_to(float(0), self.selend[1])
			cr.line_to(float(item.x2-item.x1), self.selend[1])
			cr.stroke()
			return
		if self.toggle_table_column_splitter.get_active() and self.selend[0]:
			cr.set_source_rgba(0,255,0,255)
			cr.move_to(self.selend[0],float(0))
			cr.line_to(self.selend[0],float(item.y2-item.y1))
			cr.stroke()
			return
		if self.toggle_table_row_splitter.get_active() and self.selend[0]:
			cr.set_source_rgba(0,255,0,255)
			cr.move_to(float(0), self.selend[1])
			cr.line_to(float(item.x2-item.x1), self.selend[1])
			cr.stroke()
			return
		if item.getType()=="Table":
			for x in item.colSep:
				cr.set_source_rgba(255,255,0,255)
				cr.move_to(x,float(0))
				cr.line_to(x,float(item.y2-item.y1))
				cr.stroke()
			for y in item.rowSep:
				cr.set_source_rgba(255,255,0,255)
				cr.move_to(float(0), y)
				cr.line_to(float(item.x2-item.x1), y)
				cr.stroke()
		for i, child in enumerate(item.children):
			x1 = (child.x1-item.x1)
			y1 = (child.y1-item.y1)
			x2 = (child.x2-item.x1)
			y2 = (child.y2-item.y1)
			if i in self.ctie.selections:
				cr.set_source_rgba(0,0,255,255)
				if self.mode=='move':
					cr.rectangle(x1+xoff, y1+yoff, x2-x1, y2-y1)
				elif self.mode=='resize':
					xoff2 = max(xoff,x1-x2)
					yoff2 = max(yoff,y1-y2)
					cr.rectangle(x1, y1, x2-x1+xoff2, y2-y1+yoff2)
				else:
					cr.rectangle(x1, y1, x2-x1, y2-y1)
			else:
				cr.set_source_rgba(255,0,0,255)
				cr.rectangle(x1, y1, x2-x1, y2-y1)
			cr.stroke()
		if self.toggle_childrenpath.get_active():
			cr.set_source_rgba(0,255,0,255)
			for i,child in enumerate(item.children):
				xa = (child.x1+child.x2)/2-item.x1
				ya = (child.y1+child.y2)/2-item.y1
				if i in self.ctie.selections:
					if self.mode=='move':
						xa += xoff
						ya += yoff
					elif self.mode=='resize':
						xoff2 = max(xoff,x1-x2)
						yoff2 = max(yoff,y1-y2)
						xa += xoff2/2
						ya += yoff2/2
				if i==0:
					cr.move_to(xa,ya)
				else:
					cr.line_to(xa,ya)
			cr.stroke()
			if self.ctie.selections:
				cr.set_line_width(3)
				cr.set_source_rgba(0,0,0,255)
				for i,child in enumerate(item.reordered_children()):
					xa = (child.x1+child.x2)/2-item.x1
					ya = (child.y1+child.y2)/2-item.y1
					if i in self.ctie.selections:
						if self.mode=='move':
							xa += xoff
							ya += yoff
						elif self.mode=='resize':
							xoff2 = max(xoff,x1-x2)
							yoff2 = max(yoff,y1-y2)
							xa += xoff2/2
							ya += yoff2/2
					if i==0:
						cr.move_to(xa,ya)
					else:
						cr.line_to(xa,ya)
				cr.stroke()
				cr.set_line_width(1)
		if self.selstart!=(None, None) and self.selend!=(None, None) and len(self.ctie.selections)==0:
			cr.set_source_rgba(255,0,255,255)
			cr.rectangle(sx1, sy1, sx-sx1, sy-sy1)
			cr.stroke()
			self.set_status('Box (%d,%d) -> (%d, %d)' % (sx1, sy1, sx, sy))
		elif self.mode=='resize':
			self.set_status('Resize (%d,%d)' % (xoff, yoff))
		elif self.mode=='move':
			self.set_status('Move (%d,%d)' % (xoff, yoff))

	def preview_draw(self, widget, cr):
		item = self.ctie.getCurrentItem()
		if item is None:
			return
		if len(self.ctie.selections)!=1:
			return
		child = item.children[self.ctie.selections[0]]
		width = child.x2-child.x1
		height = child.y2-child.y1

		self.canvas.set_size_request(width, height)

		child.draw(self.preview_canvas, cr, 1)

	def zoom_fit(self, *arg):
		item = self.ctie.getCurrentItem()
		if item is None or not self.canvas:
			return
		workarea_window = self.builder.get_object('workarea_window')
		alloc = workarea_window.get_allocation()
		win_width = alloc.width
		win_height = alloc.height
		width = item.x2-item.x1
		height = item.y2-item.y1
		if width>win_width*0.8:
			self.zoom = (win_width*0.8/width)*100
		else:
			self.zoom = 100
		self.canvas.queue_draw()

	def zoom_100(self, *arg):
		if not self.canvas:
			return
		self.zoom = 100
		self.canvas.queue_draw()

	def zoom_in(self, *arg):
		if not self.canvas:
			return
		self.zoom += 5
		self.canvas.queue_draw()

	def zoom_out(self, *arg):
		if not self.canvas:
			return
		if self.zoom>5:
			self.zoom -= 5
		self.canvas.queue_draw()

	def remove_item(self, *arg):
		item = self.ctie.getCurrentItem()
		if item is None:
			return
		item.remove()

	def add_item(self, *arg):
		filec = Gtk.FileChooserDialog("Add", self.builder.get_object("main_window"), Gtk.FileChooserAction.OPEN | Gtk.FileChooserAction.SELECT_FOLDER, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_ADD, Gtk.ResponseType.ACCEPT))
		filec.set_select_multiple(True)
		if Gtk.Dialog.run(filec)==Gtk.ResponseType.ACCEPT:
			self.ctie.bulkMode = True
			cs = filec.get_filenames()
			cs.sort(natcmp)
			for path in cs:
				self.ctie.addItemByPath(path)
			filec.destroy()
			self.ctie.bulkMode = False
			self.onItemTreeChanged()
		else:
			filec.destroy()
			return

	def change_level(self, *arg):
		level = self.builder.get_object("level").get_active_text()
		if level is None:
			return
		level = int(level)
		if self.ctie.setLevel(level):
			self.focus_field = (None, None)

	def items_filter_apply(self, *arg):
		r = self.ctie.setFilter(self.builder.get_object("items_filter").get_text())
		if not r:
			self.set_status('Failed parsing filter')

	def redraw_items_list(self, *arg):
		items_list = self.builder.get_object("items_list")
		for c in items_list.get_children():
			items_list.remove(c)
		for idx, item in enumerate(self.ctie.items):
			if hasattr(item, "ui"):
				evtbox = item.ui
			else:
				evtbox = Gtk.EventBox()
				box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
				label = Gtk.Label(os.path.basename(item.path))
				canvas = Gtk.DrawingArea()
				canvas.connect("draw", item.drawThumbnail)
				canvas.set_size_request(160, 240)
				box.pack_start(canvas, False, False, 0)
				box.pack_start(label, False, False, 0)
				evtbox.add(box)
				evtbox.p = item
				item.ui = evtbox
			evtbox.index = idx
			evtbox.get_style_context().add_provider(self.css, 10)
			evtbox.connect("button-press-event", self.item_button_press)
			items_list.pack_start(evtbox, False, False, 5)
			evtbox.show_all()

	def set_children_order(self, *arg):
		if not self.toggle_childrenpath:
			self.set_status("Please enable areas path display")
			return
		self.ctie.reorder_children()

	def level_sanitize(self):
		level = self.builder.get_object("level")
		l = self.ctie.getLevel()
		try:
			active = int(level.get_active_text())
		except:
			active = 0
		level.remove_all()
		for i in range(0,l):
			level.append_text(str(i))
		if active<l:
			level.set_active(active)
			self.ctie.setLevel(active)
		else:
			level.set_active(l-1)
			self.ctie.setLevel(l-1)

	def item_button_press(self, obj, evt):
		if evt.button==1 and evt.type==Gdk.EventType.BUTTON_PRESS:
			self.ctie.selectItemByIndex(obj.index)

	def tags_refresh(self, *arg):
		item = self.ctie.getCurrentItem()
		if item is None:
			return
		self.builder.get_object('tags_pane').show_all()

		tagsbox = self.builder.get_object('tags')
		c = tagsbox.get_child()
		if c:
			tagsbox.remove(c)
		collation_editor = self.builder.get_object("collation_editor")
		collation_editor.master = None
		collation_editor.set_text("")

		grid_i = 0
		tags_table = Gtk.Grid()
		tagsbox.add(tags_table)

		types = item.getTypes()
		if types:
			group = None
			for t in types:
				radio = Gtk.RadioButton.new_with_label_from_widget(group, t)
				group = radio
				if t == item.getType():
					radio.set_active(True)
				else:
					radio.set_active(False)
				radio.connect('toggled', self.set_type, (item, t))
				tags_table.attach(radio,0,grid_i,3,1)
				grid_i += 1

		tags = self.ctie.getTags(item)
		for tag in self.ctie.tags:
			text = Gtk.Entry()
			text.set_text(tags[tag])
			text.connect('changed', self.set_tag, (item, tag))
			text.connect("focus-in-event", self.entry_focus, ('p', item, tag))
			if self.focus_field[0]=='p' and self.focus_field[1]==tag:
				self.focus_entry = text
			label = Gtk.Label(tag)
			button = Gtk.Button()
			btn_img = Gtk.Image.new_from_stock(Gtk.STOCK_CLEAR, Gtk.IconSize.BUTTON)
			button.set_image(btn_img)
			button.connect("clicked", self.clear_tag, (item, tag))
			tags_table.attach(label,0,grid_i,1,1)
			tags_table.attach(text,1,grid_i,1,1)
			tags_table.attach(button,2,grid_i,1,1)
			grid_i += 1
		tagsbox.show_all()
		GObject.idle_add(self.autofocus)
		self.child_tags_refresh()

	def set_type(self, obj, data):
		item, t = data
		if obj.get_active():
			item.setType(t)

	def child_tags_refresh(self, *arg):
		item = self.ctie.getCurrentItem()
		if item is None:
			return

		tagsbox = self.builder.get_object('child_tags')
		c = tagsbox.get_child()
		if c:
			tagsbox.remove(c)

		if len(self.ctie.selections)!=1:
			return

		child = item.children[self.ctie.selections[0]]
		tags = self.ctie.getTags(child)

		grid_i = 0
		tags_table = Gtk.Grid()
		tagsbox.add(tags_table)

		types = child.getTypes()
		if types:
			group = None
			for t in types:
				radio = Gtk.RadioButton.new_with_label_from_widget(group, t)
				group = radio
				if t == child.getType():
					radio.set_active(True)
				else:
					radio.set_active(False)
				radio.connect('toggled', self.set_type, (child, t))
				tags_table.attach(radio,0,grid_i,3,1)
				grid_i += 1

		for key in self.ctie.tags:
			text = Gtk.Entry()
			text.set_text(tags[key])
			text.connect('changed', self.set_tag, (child, key))
			text.connect("focus-in-event", self.entry_focus, ('c', child, key))

			if self.focus_field[0]=='c' and self.focus_field[1]==key:
				self.focus_entry = text
			label = Gtk.Label(key)
			button = Gtk.Button()
			btn_img = Gtk.Image.new_from_stock(Gtk.STOCK_CLEAR, Gtk.IconSize.BUTTON)
			button.set_image(btn_img)
			button.connect("clicked", self.clear_tag, (child, key))
			tags_table.attach(label,0,grid_i,1,1)
			tags_table.attach(text,1,grid_i,1,1)
			tags_table.attach(button,2,grid_i,1,1)
			grid_i += 1
		tagsbox.show_all()
		self.collation_cb(None)
		GObject.idle_add(self.autofocus)

	def autofocus(self, *arg):
		if self.focus_entry:
			if not self.focus_entry.get_text():
				auto_fill = self.builder.get_object("auto_fill").get_active_text()
				if auto_fill=="Clipboard":
					self.focus_entry.paste_clipboard()
					GObject.idle_add(self.autofocus2)
				self.focus_entry.grab_focus()
			else:
				self.focus_entry.grab_focus()
				self.focus_entry = None

	def autofocus2(self, *arg):
		if not self.focus_entry:
			return
		self.focus_entry.set_position(-1)
		self.focus_entry = None

	def entry_focus(self, obj, evt, data, *arg):
		t,item,tag = data
		self.focus_field = (t,tag)
		self.collation_cb(obj)

	def set_tag(self, obj, data):
		item, key = data
		item.setTag(key, obj.get_buffer().get_text())
		self.collation_cb(obj)

	def collation_cb(self, obj, *arg):
		if self.toggle_collation.get_active() and self.focus_field and self.focus_field[0]=='c':
			self.builder.get_object("editor_label").set_text(self.focus_field[1])
			self.builder.get_object("collation_window").show()
			self.builder.get_object("collation_editor").master = obj
			if not self.signal_mask and obj:
				GObject.idle_add(self.focus_collation_editor)
				self.signal_mask = True
				self.builder.get_object("collation_editor").set_text(obj.get_text())
				self.signal_mask = False
		else:
			self.builder.get_object("collation_window").hide()

	def focus_collation_editor(self):
		self.builder.get_object("collation_editor").grab_focus()
		GObject.idle_add(self.focus_collation_editor2)

	def focus_collation_editor2(self, *arg):
		self.builder.get_object("collation_editor").set_position(0)

	def collation_editor_changed(self, obj, *arg):
		master = obj.master
		if master and not self.signal_mask:
			self.signal_mask = True
			master.set_text(obj.get_text())
			self.signal_mask = False

	def clear_tag(self, obj, data):
		item, key = data

	def onItemListChanged(self):
		self.uiItemList.reset()

	def onItemChanged(self):
		self.uiWorkArea.onItemChanged()
		# self.preview_canvas.queue_draw()
		# self.zoom_fit()
		# self.tags_refresh()

	def onSelectionChanged(self):
		self.child_tags_refresh()
		if self.preview_canvas:
			self.preview_canvas.queue_draw()
		if self.canvas:
			self.canvas.queue_draw()
		item = self.ctie.getCurrentItem()
		if item:
			self.set_status('Area: %d Select: %s' % (len(item.children), ', '.join([str(i+1) for i in self.ctie.selections])))

	def onItemTreeChanged(self):
		if self.ctie.bulkMode:
			return
		self.level_sanitize()

	def onTagChanged(self):
		self.tags_refresh()

	def onItemRemoved(self, item):
		items_list = self.builder.get_object("items_list")
		items_list.remove(item.ui)
		item.ui.destroy()
		del item.ui

	def onItemFocused(self):
		item = self.ctie.getCurrentItem()
		if not item:
			return
		self.uiItemList.scrollTo(item.ui)
		self.set_status("Item: %d/%d" % (self.ctie.getCurrentItemIndex()+1, len(self.ctie.items)))
		if hasattr(item, "ui"):
			item.ui.setStyleSheet("background-color:rgba(50,50,255,30);");
		# XXX
		# if self.toggle_ocr.get_active():
		# 	if self.toggle_collation.get_active():
		# 		for child in item.children:
		# 			child.ocr()
		# 		self.ctie.selectChildByIndex(0)
		# 	else:
		# 		item.ocr()

	def onItemBlurred(self, item):
		if not item is None and hasattr(item, "ui"):
			item.ui.setStyleSheet("background-color:auto;");

	def workarea_mouse(self, obj, evt):
		item = self.ctie.getCurrentItem()
		if item is None or not self.canvas:
			return
		self.focus_field = (None, None)
		self.canvas.grab_focus()
		factor = self.zoom*0.01
		evtx,evty = self.builder.get_object('workarea').translate_coordinates(self.canvas, evt.x, evt.y)
		x = evtx/factor
		y = evty/factor
		if str(type(evt))==repr(Gdk.EventButton):
			if evt.button==1 and evt.type==Gdk.EventType.BUTTON_PRESS:
				self.selstart = (x, y)
				self.selend = (x, y)
				if not len(self.ctie.selections):
					self.mode = 'rectangle'
				else:
					for i in self.ctie.selections:
						child = item.children[i]
						if child.contains(x+item.x1, y+item.y1):
							self.mode = 'move'
							break
					else:
						self.mode = 'resize'
			elif evt.button==1 and evt.type==Gdk.EventType.BUTTON_RELEASE:
				if self.toggle_horizontal_splitter.get_active() and self.selend[0]:
					x = self.selend[0]
					item.addChild(x1 = item.x1, y1 = item.y1, x2 = item.x1+x, y2 = item.y2)
					item.addChild(x1 = item.x1+x, y1 = item.y1, x2 = item.x2, y2 = item.y2)
				elif self.toggle_vertical_splitter.get_active() and self.selend[0]:
					y = self.selend[1]
					item.addChild(x1 = item.x1, y1 = item.y1, x2 = item.x2, y2 = item.y1+y)
					item.addChild(x1 = item.x1, y1 = item.y1+y, x2 = item.x2, y2 = item.y2)
				elif self.toggle_table_row_splitter.get_active() and self.selend[0] and item.getType()=="Table":
					y = self.selend[1]
					item.addRowSep(y)
				elif self.toggle_table_column_splitter.get_active() and self.selend[0] and item.getType()=="Table":
					x = self.selend[0]
					item.addColSep(x)
				else:
					x1,y1 = self.selstart
					if (x1,y1)==(None, None):
						return
					if x1==x and y1==y:
						for i, child in enumerate(item.children):
							if child.contains(x+item.x1, y+item.y1):
								if i in self.ctie.selections:
									self.ctie.deselectChildByIndex(i)
								else:
									self.ctie.selectChildByIndex(i)
					elif self.mode=='rectangle':
						if x1>x:
							x1, x = x, x1
						if y1>y:
							y1, y = y, y1
						x1 = max(x1, 0)
						y1 = max(y1, 0)
						x = min(x, item.x2-item.x1)
						y = min(y, item.y2-item.y1)
						if x-x1>5 and y-y1>5:
							item.addChild(x1 = x1+item.x1, y1 = y1+item.y1, x2 = x+item.x1, y2 = y+item.y1)
					elif self.mode=='move':
						xoff = self.selend[0]-self.selstart[0]
						yoff = self.selend[1]-self.selstart[1]
						self.ctie.move(xoff, yoff)
					elif self.mode=='resize':
						xoff = self.selend[0]-self.selstart[0]
						yoff = self.selend[1]-self.selstart[1]
						self.ctie.resize(xoff, yoff)
				self.selstart = (None, None)
				self.selend = (None, None)
				self.mode = None
				self.canvas.queue_draw()
				self.preview_canvas.queue_draw()
			elif evt.button==3:
				self.selstart = (None, None)
		elif isinstance(evt, Gdk.EventMotion):
			self.selend = (x,y)
			self.canvas.queue_draw()
		elif isinstance(evt, Gdk.EventScroll) and evt.state & Gdk.ModifierType.CONTROL_MASK:
			if evt.direction==Gdk.ScrollDirection.UP:
				self.zoom += 5
			elif evt.direction==Gdk.ScrollDirection.DOWN:
				self.zoom -= 5
			self.canvas.queue_draw()
			return False
