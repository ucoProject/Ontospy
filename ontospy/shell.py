#!/usr/bin/env python


"""
OntoSPy Shell Module
michele.pasin@gmail.com

# docs:
# https://docs.python.org/2/library/cmd.html
# https://hg.python.org/cpython/file/2.7/Lib/cmd.py
# http://pymotw.com/2/cmd/

# Colorama cheatsheet: https://pypi.python.org/pypi/colorama
# Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Style: DIM, NORMAL, BRIGHT, RESET_ALL

"""



import sys, os, cmd, random, urllib2, shutil, platform
from colorama import Fore, Back, Style
from pyfiglet import Figlet

from subprocess import PIPE, Popen
PY2 = sys.version < '3'
WINDOWS = os.name == 'nt'
EOL = '\r\n' if WINDOWS and not PY2 else '\n'


from . import ontospy
from . import _version 
from .core.util import *
from .core.quotes import QUOTES





f = Figlet(font='slant')
_intro_ = """***											  
The Command Line Ontology Browser (%s) 
***											  """

STARTUP_MESSAGE = f.renderText('OntoSPy') + Style.BRIGHT + _intro_ % _version.VERSION + Style.RESET_ALL




def _get_prompt(onto="", entity="", defaultP=Fore.RED, defaultE=Fore.BLUE):
	""" 
	Global util that changes the prompt contextually 
	<defaultP> = color of 'Ontospy'
	<defaultE> = color of subsequent entity
	"""
	onto_c, entity_c = "", ""
	base = defaultP + Style.BRIGHT +'[OntoSPy]' + Style.RESET_ALL
	if onto and not entity:
		temp1 = defaultE + '[%s]' % onto 
		onto_c = defaultE + Style.BRIGHT + temp1 + Style.RESET_ALL
	if entity:
		# onto = self.current['file']
		temp1_1 = defaultE + Style.NORMAL + '[%s]' % truncate(onto, 10)
		temp1_2 = defaultE + Style.BRIGHT + '[%s]' % entity
		entity_c = defaultE + Style.BRIGHT + temp1_1 + temp1_2 + Style.RESET_ALL

	return base + onto_c + entity_c + "> "



class Shell(cmd.Cmd):
	"""Simple command processor example."""

	prompt = _get_prompt()
	intro = "Type 'help' to get started, TAB to explore commands.\n"

	doc_header = 'Commands available (type `help <command>` to get help):'
	misc_header = 'Miscellaneous'
	undoc_header = 'Undocumented commands'
	
	ruler = '-'
	maxcol = 80
	
	DISPLAY_OPTS = ['toplayer', 'parents', 'children', 'triples' ]
	SERIALIZE_OPTS = ['xml', 'n3', 'turtle', 'nt', 'pretty-xml', 'json-ld']
	LS_OPTS = ['ontologies', 'classes', 'properties', 'concepts', 'namespaces']
	GET_OPTS = ['ontology', 'class', 'property', 'concept']
	FILE_OPTS = ['rename', 'delete']
	
		
	def __init__(self):
		 """
		 self.current = {'file' : filename, 'fullpath' : fullpath, 'graph': g}
		 self.currentEntity = {'name' : obj.locale or obj.uri, 'object' : obj, 'type' : 'class'} 
																		# or 'property' or 'concept'
		 """
		 # useful vars
		 self.LOCAL = ontospy.ONTOSPY_LOCAL
		 self.LOCAL_MODELS = ontospy.get_home_location()
		 self.ontologies = ontospy.get_localontologies()
		 self.current = None
		 self.currentEntity = None
		 
		 cmd.Cmd.__init__(self)



	# BASE CLASSE OVERRIDES:
	# --------	
	
	def emptyline(self):
		""" override default behaviour of running last command """
		pass
		
	def print_topics(self, header, cmds, cmdlen, maxcol):
		"""Override 'print_topics' so that you can exclude EOF and shell.
			2016-02-12: added to test, copied from 
			https://github.com/xlcnd/isbntools/blob/master/isbntools/bin/repl.py 
		"""
		if header:
			if cmds:
				self.stdout.write("%s\n" % str(header))
				if self.ruler:
					self.stdout.write("%s\n" % str(self.ruler * len(header)))
				self.columnize(cmds, maxcol - 1)
				self.stdout.write("\n") 


	def default(self, line):
		"default message when a command is not recognized"
		foo = ["Don't recognize that command. Try 'help' for some suggestions.", "That looks like the wrong command", "Are you sure you mean that? Try 'help' for some suggestions."]
		self._print(random.choice(foo))
		
		

	# HELPER METHODS
	# --------	

	def _print(self, ms, style="TIP"):
		""" abstraction for managing color printing """
		styles1 = {'IMPORTANT' : Style.BRIGHT, 
					'TIP': Style.DIM, 
					'URI' : Style.BRIGHT,  
					'TEXT' : Fore.GREEN, 
					'MAGENTA' : Fore.MAGENTA ,
					'BLUE' : Fore.BLUE ,
					'GREEN' : Fore.GREEN ,
					'RED' : Fore.RED ,
					'DEFAULT' : Style.DIM ,
					}
		try:
			print styles1[style] + ms + Style.RESET_ALL 
		except:
			print styles1['DEFAULT'] + ms + Style.RESET_ALL

	def _printM(self, messages):
		"""print a list of strings - for the mom used only by stats printout"""
		if len(messages) == 2:
			print Style.BRIGHT + messages[0] + Style.RESET_ALL + Fore.BLUE + messages[1] + Style.RESET_ALL
		else:
			print "Not implemented"


	def _joinedQnames(self, _list):
		"""util for returning a string joinin names of entities *used only in info command*"""
		try:
			s = "; ".join([p.qname for p in _list])
		except:
			s = "; ".join([p for p in _list])
		return s
		


	def _clear_screen(self):
		""" http://stackoverflow.com/questions/18937058/python-clear-screen-in-shell """
		if platform.system() == "Windows":
			tmp = os.system('cls') #for window
		else:
			tmp = os.system('clear') #for Linux
		return True


	def _printTriples(self, entity):
		""" display triples """
		self._print("----------------", "TIP")
		self._print(unicode(entity.uri) , "IMPORTANT")
		for x in entity.triples:
			self._print("=> " + unicode(x[1]) , "MAGENTA")
			self._print(".... " + unicode(x[2]) , "GREEN")
		self._print("----------------", "TIP")


	def _print_entity_intro(self, g=None, entity=None, first_time=True):
		"""after a selection, prints on screen basic info about onto or entity, plus change prompt 
		2015-10-18: removed the sound
		2016-01-18: entity is the shell wrapper around the ontospy entity
		"""
		if entity:
			self._clear_screen()
			obj = entity['object']
			self._print("Loaded %s: <%s>" % (entity['type'].capitalize(), str(obj.uri)), "TIP")
			self._print("----------------", "TIP")
			# self._print(obj.bestDescription(), "TEXT")
			if first_time:
				self.prompt = _get_prompt(self.current['file'], self.currentEntity['name'])
		elif g:
			self._printDescription(False)
			if first_time:
				self.prompt = _get_prompt(self.current['file'])



	# def _printStats(self, hrlinetop=True):
	# 	"""
	# 	print more informative stats about the object
	# 	2016-04-21: created more specific methods. THis will be eventually removed!
	# 	"""
	# 	if hrlinetop:
	# 		self._print("----------------")
	# 	if not self.currentEntity:	# ==> ontology level 
	# 		g = self.current['graph']			
	# 		self._print("Ontologies......: %d" % len(g.ontologies))
	# 		self._print("Classes.........: %d" % len(g.classes))
	# 		self._print("Properties......: %d" % len(g.properties))
	# 		self._print("..annotation....: %d" % len(g.annotationProperties))
	# 		self._print("..datatype......: %d" % len(g.datatypeProperties))
	# 		self._print("..object........: %d" % len(g.objectProperties))
	# 		self._print("Concepts(SKOS)..: %d" % len(g.skosConcepts))
	# 		self._print("----------------")

	# 	elif self.currentEntity['type'] == 'class':
	# 		x = self.currentEntity['object']
	# 		self._printM(["Parents......[%d]\x20\x20" % len(x.parents()), self._joinedQnames(x.parents())])
	# 		self._printM(["\nAncestors....[%d]\x20\x20" % len(x.ancestors()), self._joinedQnames(x.ancestors())])
	# 		self._printM(["\nChildren.....[%d]\x20\x20" % len(x.children()), self._joinedQnames(x.children())])
	# 		self._printM(["\nDescendants..[%d]\x20\x20" % len(x.descendants()), self._joinedQnames(x.descendants())])
	# 		self._printM(["\nIn Domain of.[%d]\x20\x20" % len(x.domain_of), self._joinedQnames(x.domain_of)])
	# 		self._printM(["\nIn Range of..[%d]\x20\x20" % len(x.range_of), self._joinedQnames(x.range_of)])
	# 		self._printM(["\nInstances....[%d]\x20\x20" % len(x.all()), self._joinedQnames(x.all())])
	# 		self._print("----------------")
																			
	# 	elif self.currentEntity['type'] == 'property':
	# 		x = self.currentEntity['object']
	# 		self._printM(["Parents......[%d]\x20\x20" % len(x.parents()), self._joinedQnames(x.parents())])
	# 		self._printM(["\nAncestors....[%d]\x20\x20" % len(x.ancestors()), self._joinedQnames(x.ancestors())])
	# 		self._printM(["\nChildren.....[%d]\x20\x20" % len(x.children()), self._joinedQnames(x.children())])
	# 		self._printM(["\nDescendants..[%d]\x20\x20" % len(x.descendants()), self._joinedQnames(x.descendants())])
	# 		self._printM(["\nHas Domain ..[%d]\x20\x20" % len(x.domains), self._joinedQnames(x.domains)])
	# 		self._printM(["\nHas Range ...[%d]\x20\x20" % len(x.ranges), self._joinedQnames(x.ranges)])
	# 		self._print("----------------")

	# 	elif self.currentEntity['type'] == 'concept':
	# 		x = self.currentEntity['object']
	# 		self._printM(["Parents......[%d]\x20\x20" % len(x.parents()), self._joinedQnames(x.parents())])
	# 		self._printM(["\nAncestors....[%d]\x20\x20" % len(x.ancestors()), self._joinedQnames(x.ancestors())])
	# 		self._printM(["\nChildren.....[%d]\x20\x20" % len(x.children()), self._joinedQnames(x.children())])
	# 		self._printM(["\nDescendants..[%d]\x20\x20" % len(x.descendants()), self._joinedQnames(x.descendants())])
	# 		self._print("----------------")

	# 	else:
	# 		self._print("Not implemented") 


	def _printDescription(self, hrlinetop=True):
		"""generic method to print out a description"""
		if hrlinetop:
			self._print("----------------")
		NOTFOUND = "[not found]"
		if self.currentEntity:
			obj = self.currentEntity['object']
			label = obj.bestLabel() or NOTFOUND
			description = obj.bestDescription() or NOTFOUND
			print Style.BRIGHT + "Object Type: " + Style.RESET_ALL + Fore.BLACK + uri2niceString(obj.rdftype) + Style.RESET_ALL
			print Style.BRIGHT + "URI        : " + Style.RESET_ALL+ Fore.GREEN + unicode(obj.uri) + Style.RESET_ALL
			print Style.BRIGHT + "Title      : " + Style.RESET_ALL+ Fore.BLACK + label + Style.RESET_ALL
			print Style.BRIGHT + "Description: " + Style.RESET_ALL+ Fore.BLACK + description + Style.RESET_ALL
				
		else:
			self._clear_screen()
			self._print("Graph: <" + self.current['fullpath'] + ">", 'TIP')
			self._print("----------------", "TIP")
			self.current['graph'].printStats()
			for obj in self.current['graph'].ontologies:
				self._print("==> Ontology URI: <%s>" % str(obj.uri), "IMPORTANT")
				self._print("----------------", "TIP")
				label = obj.bestLabel() or NOTFOUND
				description = obj.bestDescription() or NOTFOUND
				print Style.BRIGHT + "Title      : " + Style.RESET_ALL+ Fore.GREEN + label + Style.RESET_ALL
				print Style.BRIGHT + "Description: " + Style.RESET_ALL+ Fore.GREEN + description + Style.RESET_ALL
		self._print("----------------", "TIP")
		


	def _printTaxonomy(self, hrlinetop=True):
		"""
		print a local taxonomy for the object
		"""
		if not self.currentEntity:	# ==> ontology level 
			return
		if hrlinetop:
			self._print("----------------")
		self._print("Taxonomy:", "IMPORTANT")
		x = self.currentEntity['object']
		parents = x.parents()
								
		if not parents:
			if self.currentEntity['type'] == 'class':
				self._print("OWL:Thing")
			elif self.currentEntity['type'] == 'property':
				self._print("RDF:Property")
			elif self.currentEntity['type'] == 'concept':
				self._print("SKOS:Concept")
			else:
				pass
		else:
			for p in parents:
				self._print(p.qname)
		self._print("..." + x.qname, "TEXT")
		for c in x.children():
			self._print("......" + c.qname)
		self._print("----------------")
		


	def _printClassDomain(self, hrlinetop=True):
		"""
		print more informative stats about the object
		"""
		if not self.currentEntity:	# ==> ontology level 
			return
		x = self.currentEntity['object']	
		if self.currentEntity['type'] == 'class':
			if hrlinetop:
				self._print("----------------")
			self._print("Domain Of: [%d]" % len(x.domain_of), "IMPORTANT")
			for i in x.domain_of:
				self._print(i.qname)
			self._print("----------------")	
		return 

	def _printClassRange(self, hrlinetop=True):
		"""
		print more informative stats about the object
		"""
		if not self.currentEntity:	# ==> ontology level 
			return
		x = self.currentEntity['object']	
		if self.currentEntity['type'] == 'class':
			if hrlinetop:
				self._print("----------------")
			self._print("Range Of: [%d]" % len(x.range_of), "IMPORTANT")
			for i in x.range_of:
				self._print(i.qname)
			self._print("----------------")	
		return 


	def _printPropertyDomainRange(self, hrlinetop=True):
		"""
		print more informative stats about the object
		"""
		if not self.currentEntity:	# ==> ontology level 
			return
		x = self.currentEntity['object']	
		if self.currentEntity['type'] == 'property':
			if hrlinetop:
				self._print("----------------")
			self._print("Usage:", "IMPORTANT")
			domains = x.domains
			ranges = x.ranges
			if x.domains:
				for d in x.domains:
					self._print(d.qname)
			else:
				self._print("OWL:Thing")
			self._print("  " + "<" + x.qname + ">", "TEXT")	
			if x.ranges:
				for d in x.ranges:
					self._print("  " + "   => " + d.qname)
			else:
				self._print("  " + "   => " + "OWL:Thing")
			self._print("----------------")	
		return 


	def _printInstances(self, hrlinetop=True):
		"""
		print more informative stats about the object
		"""
		if not self.currentEntity:	# ==> ontology level 
			return
		x = self.currentEntity['object']	
		if self.currentEntity['type'] == 'class':
			if hrlinetop:
				self._print("----------------")
			self._print("Instances: [%d]" % len(x.all()), "IMPORTANT")
			for i in x.all():
				self._print(i.qname)
			self._print("----------------")	
		return 


	def _printSourceCode(self, hrlinetop=True):
		"""
		print more informative stats about the object
		"""
		if not self.currentEntity:	# ==> ontology level 
			return
		x = self.currentEntity['object']	
		if hrlinetop:
			self._print("----------------")

		self._print("Source:", "IMPORTANT")
		self.do_serialize("turtle")
		self._print("----------------")	

		return 



	def _selectFromList(self, _list, using_pattern=True):
		"""
		Generic method that lets users pick an item from a list via raw_input
		*using_pattern* flag to know if we're showing all choices or not
		Note: the list items need to be OntoSPy entities.
		"""
		if not _list:
			self._print("No matching items.", "TIP")
			return None
		if using_pattern and len(_list) == 1: # removed
			pass
			# return _list[0]
		if using_pattern:
			self._print("%d matching items: \n--------------" % len(_list), "TIP")
		else:
			self._print("%d items available: \n--------------" % len(_list), "TIP")
		counter = 1
		_temp = []
		for el in _list:
			if hasattr(el, 'qname'):
				_temp += [Fore.BLUE + Style.BRIGHT + "[%d] " % counter + Style.RESET_ALL + str(el.qname)]
			elif hasattr(el, 'uri'):
				_temp += [Fore.BLUE + Style.BRIGHT + "[%d] " % counter + Style.RESET_ALL + str(el.uri)]
			else:
				_temp += [Fore.BLUE + Style.BRIGHT + "[%d] " % counter + Style.RESET_ALL + str(el)]
			counter += 1
		pprint2columns(_temp)
		
		self._print("--------------")
		self._print("Please select one option by entering its number: ")
		var = raw_input()
		try:
			var = int(var)
			return _list[var-1]
		except:
			self._print("Selection not valid")
			return None


	def _next_ontology(self):
		"""Dynamically retrieves the next ontology in the list"""
		currentfile = self.current['file']
		try:
			idx = self.ontologies.index(currentfile)
			return self.ontologies[idx+1]
		except:
			return self.ontologies[0]



	# MAIN METHODS
	# --------


	def _load_ontology(self, filename):
		""" loads an ontology from the local repository 
			note: if the ontology does not have a cached version, it is created
		"""
		fullpath = self.LOCAL_MODELS + filename
		g = ontospy.get_pickled_ontology(filename)
		if not g:
			g = ontospy.do_pickle_ontology(filename)
		self.current = {'file' : filename, 'fullpath' : fullpath, 'graph': g}
		self.currentEntity = None
		self._print_entity_intro(g)


	def _select_ontology(self, line):
		"""try to select an ontology NP: the actual load from FS is in <_load_ontology> """
		try:
			var = int(line)	 # it's a string
			if var in range(1, len(self.ontologies)+1):
				self._load_ontology(self.ontologies[var-1])
		except ValueError:
			out = []
			for each in self.ontologies:
				if line in each:
					out += [each]
			choice = self._selectFromList(out, line)
			if choice:
				self._load_ontology(choice)


	def _select_class(self, line):			
		"""try to match a class and load it from the graph"""	
		g = self.current['graph']
		if not line:
			out = g.classes
			using_pattern=False
		else:
			using_pattern=True
			if line.isdigit():
				line =	int(line)
			out = g.getClass(line)
		if out:
			if type(out) == type([]):
				choice = self._selectFromList(out, using_pattern)
				if choice:
					self.currentEntity = {'name' : choice.locale or choice.uri, 'object' : choice, 'type' : 'class'}				
			else:
				self.currentEntity = {'name' : out.locale or out.uri, 'object' : out, 'type' : 'class'}				
			# ..finally:
			if self.currentEntity:
				self._print_entity_intro(entity=self.currentEntity)
				

		else:
			print "not found"


	def _select_property(self, line):			
		"""try to match a property and load it"""
		g = self.current['graph']
		if not line:
			out = g.properties
			using_pattern=False
		else:
			using_pattern=True			
			if line.isdigit():
				line =	int(line)
			out = g.getProperty(line)
		if out:
			if type(out) == type([]):
				choice = self._selectFromList(out, using_pattern)
				if choice:
					self.currentEntity = {'name' : choice.locale or choice.uri, 'object' : choice, 'type' : 'property'} 

			else:
				self.currentEntity = {'name' : out.locale or out.uri, 'object' : out, 'type' : 'property'}	
			
			# ..finally:
			if self.currentEntity:
				self._print_entity_intro(entity=self.currentEntity) 
		else:
			print "not found"
			

	def _select_concept(self, line):
		"""try to match a class and load it"""
		g = self.current['graph']
		if not line:
			out = g.skosConcepts
			using_pattern=False
		else:
			using_pattern=True
			if line.isdigit():
				line =	int(line)
			out = g.getSkosConcept(line)
		if out:
			if type(out) == type([]):
				choice = self._selectFromList(out, using_pattern)
				if choice:
					self.currentEntity = {'name' : choice.locale or choice.uri, 'object' : choice, 'type' : 'concept'}
			else:
				self.currentEntity = {'name' : out.locale or out.uri, 'object' : out, 'type' : 'concept'}
			# ..finally:
			if self.currentEntity:
				self._print_entity_intro(entity=self.currentEntity)

		else:
			print "not found"


	def _delete_file(self, line=""):
		"""	Delete an ontology
			2016-04-11: not a direct command anymore """
		
		if not self.ontologies:
			self._help_nofiles()

		else:
			out = []
			for each in self.ontologies:
				if line in each:
					out += [each]
			choice = self._selectFromList(out, line)
			if choice:
				fullpath = self.LOCAL_MODELS + "/" + choice
				if os.path.isfile(fullpath):

					self._print("--------------")
					self._print("Are you sure? [Y/N]")
					var = raw_input()
					if var == "y" or var == "Y":
						os.remove(fullpath)
						ontospy.del_pickled_ontology(choice)
						self._print("<%s> was deleted succesfully." % choice)
						self.ontologies = ontospy.get_localontologies()
					else:
						return 

				else:
					self._print("File not found.")
				# delete
				if self.current and self.current['fullpath'] == fullpath:
					self.current = None
					self.currentEntity = None
					self.prompt = _get_prompt()

		return 


	def _rename_file(self, line=""):
		"""Rename an ontology 
			2016-04-11: not a direct command anymore """
		
		if not self.ontologies:
			self._help_nofiles()
		else:
			out = []
			for each in self.ontologies:
				if line in each:
					out += [each]
			choice = self._selectFromList(out, line)
			if choice:
				fullpath = self.LOCAL_MODELS + "/" + choice
				print fullpath
				if os.path.isfile(fullpath):

					self._print("--------------")
					self._print("Please enter a new name for <%s>, including the extension (blank=abort)"  \
						% choice)
					var = raw_input()
					if var:
						try:
							os.rename(fullpath, self.LOCAL_MODELS + "/" + var)
							ontospy.rename_pickled_ontology(choice, var)
							self._print("<%s> was renamed succesfully." % choice)
							self.ontologies = ontospy.get_localontologies()
						except:
							self._print("Not a valid name. An error occurred.")
							return
					else:
						return 

				else:
					self._print("File not found.")
				# delete
				if self.current and self.current['fullpath'] == fullpath:
					self.current = None
					self.currentEntity = None
					self.prompt = _get_prompt()

		return 




	# COMMANDS
	# --------
	# NOTE: all commands should start with 'do_' and must pass 'line'



	def do_ls(self, line):
		"""Shows entities of a given kind."""
		opts = self.LS_OPTS
		line = line.split()
		_pattern = ""
	
		if len(line) == 0:
			# default contextual behaviour [2016-03-01]
			if not self.current:
				line = ["ontologies"]
			elif self.currentEntity:
				self.do_info("")	
				return	
			else:
				line = ["classes"]
		

		if (not line) or (line[0] not in opts):
			self.help_ls()
			return
			# self._print("Usage: ls [%s]" % "|".join([x for x in opts]))

		elif line[0] == "ontologies":
			if not self.ontologies:
				self._help_nofiles()
			else:
				self._select_ontology(_pattern)

		elif line[0] in opts and not self.current:
			self._help_noontology()
			return

		elif line[0] == "namespaces":			
			for x in self.current['graph'].namespaces:
				self._print("@prefix %s: <%s> ." % (x[0], x[1])) 

		elif line[0] == "classes":
			g = self.current['graph']

			if g.classes:
				if len(line) > 1 and line[1] == "tree":
					g.printClassTree(showids=False, labels=False, showtype=True)
					self._print("----------------", "TIP")
				else:
					self._select_class(_pattern)
			else:
				self._print("No classes available.")

		elif line[0] == "properties":
			g = self.current['graph']
			if g.properties:
				if len(line) > 1 and line[1] == "tree":
					g.printPropertyTree(showids=False, labels=False, showtype=True)
				else:
					self._select_property(_pattern)
			else:
				self._print("No properties available.") 

		elif line[0] == "concepts":
			g = self.current['graph']
			if g.skosConcepts:
				if len(line) > 1 and line[1] == "tree":
					g.printSkosTree(showids=False, labels=False, showtype=True)
				else:
					self._select_concept(_pattern)
			else:
				self._print("No concepts available.")	

		else: # should never arrive here
			pass


	def do_get(self, line):
		"""Finds entities matching a given string pattern. \nOptions: [ ontologies | classes | properties | concepts ]"""
		line = line.split()
		_pattern = ""
		if len(line) > 1:
			_pattern = line[1]			
		opts = self.GET_OPTS

		if (not line) or (line[0] not in opts) or (not _pattern):
			self.help_get()
			return
			# self._print("Usage: get [%s] <name>" % "|".join([x for x in opts]))

		elif line[0] == "ontology":
			if not self.ontologies:
				self._help_nofiles()
			else:
				self._select_ontology(_pattern)

		elif line[0] in opts and not self.current:
			self._help_noontology()
			return

		elif line[0] == "class":
			g = self.current['graph']
			if g.classes:
				self._select_class(_pattern)
			else:
				self._print("No classes available.")

		elif line[0] == "property":
			g = self.current['graph']
			if g.properties:
				self._select_property(_pattern)
			else:
				self._print("No properties available.") 

		elif line[0] == "concept":
			g = self.current['graph']
			if g.skosConcepts:
				self._select_concept(_pattern)
			else:
				self._print("No concepts available.")	

		else: # should never arrive here
			pass
							


	def do_display(self, line):
		"""Display information about current entity."""
		opts = self.DISPLAY_OPTS
		
		if not self.current:
			self._help_noontology()
			return
		
		line = line.split() 
		g = self.current['graph']
		
		# get arg, or default to 'overview'
		if not line:
			self.help_display()
			return

		if line[0] == "toplayer":			
			for x in g.toplayer:
				print x.qname
		
		elif line[0] == "parents":
			if self.currentEntity:
				for x in self.currentEntity['object'].parents():
					print x.qname
			else:
				self._print("Please select an entity first.") 

		elif line[0] == "children":			
			if self.currentEntity:
				for x in self.currentEntity['object'].children():
					print x.qname
			else:
				self._print("Please select an entity first.") 

		elif line[0] == "triples":	
			if self.currentEntity:
				self._printTriples(self.currentEntity['object'])
				# self.currentEntity['object'].printTriples()
			else:
				for o in g.ontologies:
					self._printTriples(o)
					# o.printTriples()
																			
		else:
			pass # never get here
				


	def do_info(self, line):
		"""Inspect the current entity and display a nice summary of key properties"""
		# opts = [ 'namespaces', 'description', 'overview', 'toplayer', 'parents', 'children', 'stats', 'triples' ]
		
		if not self.current:
			self._help_noontology()
			return 

		g = self.current['graph']
		
		self._printDescription()
		self._printTaxonomy(False)
		self._printClassDomain(False)
		self._printClassRange(False)
		self._printPropertyDomainRange(False)
		# self._printSourceCode(False)
				
		return 


	def do_visualize(self, line):
		"""Visualize an ontology - ie wrapper for export command"""

		if not self.current:
			self._help_noontology()
			return 

		line = line.split() 
		_gist = False
		if line and line[0] == "gist":
			_gist = True

		import webbrowser
		url = ontospy.action_export(args=self.current['file'], save_gist=_gist, fromshell=True)
		if url:
			webbrowser.open(url)
		return


	def do_download(self, line):
		"""Download an ontology"""

		line = line.split()

		if line and line[0] == "starter-pack":
			ontospy.action_bootstrap()
			self.ontologies = ontospy.get_localontologies()
		elif line and line[0].startswith("http"):
			try:
				ontospy.action_import(line[0])
			except:
				self._print("OPS... An Unknown Error Occurred - Aborting installation of <%s>" % line[0])

		else:
			self._print("TIP: use 'download <uri>' to download from a specific location.")
			ontospy.action_webimport_select()
			self.ontologies = ontospy.get_localontologies()
		
		return


	def do_file(self, line):
		"""PErform some file operation"""
		opts = self.FILE_OPTS
		
		if not self.ontologies:
			self._help_nofiles()
			return

		line = line.split() 

		if not line or line[0] not in opts:
			self.help_file()
			return	
		
		if line[0] == "rename":
			self._rename_file()
		elif line[0] == "delete":
			self._delete_file() 
		else:
			return


	def do_serialize(self, line):
		"""Serialize an entity into an RDF flavour"""
		opts = self.SERIALIZE_OPTS
		
		if not self.current:
			self._help_noontology()
			return
		
		line = line.split() 
		g = self.current['graph']

		if not line:
			line = ['turtle']
		
		if line[0] not in opts:
			self.help_serialize()
			return	
		
		elif self.currentEntity:
			self.currentEntity['object'].printSerialize(line[0])

		else:	
			for o in g.ontologies:
				o.printSerialize(line[0])

	
									
	def do_next(self, line):
		"""Jump to the next entities (ontology, class or property) depending on context"""
		if not self.current:
			print "Please select an ontology first. E.g. use the 'ls ontologies' or 'get ontology <name>' commands."
		elif self.currentEntity:
			g = self.current['graph']
			if self.currentEntity['type'] == 'class':
				nextentity = g.nextClass(self.currentEntity['object'].uri)
				self._select_class(str(nextentity.uri))
			elif self.currentEntity['type'] == 'property':
				nextentity = g.nextProperty(self.currentEntity['object'].uri)
				self._select_property(str(nextentity.uri))
			elif self.currentEntity['type'] == 'concept':
				nextentity = g.nextConcept(self.currentEntity['object'].uri)
				self._select_concept(str(nextentity.uri))
			else:
				print "Not implemented" 
		else:
			if len(self.ontologies) > 1:
				nextonto = self._next_ontology()
				self._load_ontology(nextonto)
			else:
				self._print("Only one ontology available in repository.")	 


	def do_back(self, line):
		"Go back one step. From entity => ontology; from ontology => ontospy top level."
		if self.currentEntity:
			self.currentEntity = None
			self.prompt = _get_prompt(self.current['file'])
		else:
			self.current = None
			self.prompt = _get_prompt()

	def do_q(self, line):
		"Quit: exit the OntoSPy shell"
		self._clear_screen()
		return True


	def do_zen(self, line):
		"""Inspiring quotes for the working ontologist"""
		_quote = random.choice(QUOTES)
		# print _quote['source']
		print Style.DIM + unicode(_quote['text'])
		print Style.BRIGHT + unicode(_quote['source']) + Style.RESET_ALL


	# 2016-02-12: method taken from https://github.com/xlcnd/isbntools/blob/master/isbntools/bin/repl.py
	# 2016-04-25: hidden
	def _do_shell(self, line):
		"""Send a command to the Unix shell.\n==> Usage: shell ls ~"""
		if not line:
			return
		sp = Popen(line,
				   shell=True,
				   stdin=PIPE,
				   stdout=PIPE,
				   stderr=PIPE,
				   close_fds=not WINDOWS)
		(fo, fe) = (sp.stdout, sp.stderr)
		if PY2:
			out = fo.read().strip(EOL)
			err = fe.read().strip(EOL)
		else:
			out = fo.read().decode("utf-8")
			err = fe.read().decode("utf-8")
		if out:
			print(out)
			return
		if err:
			print(err.replace('isbn_', ''))




	# HELP METHODS
	# --------	

	def help_ls(self):
		txt = "List available graphs or entities .\n"
		txt += "==> Usage: ls [%s]" % "|".join([x for x in self.LS_OPTS])		
		txt += "\n\nUsing the *tree* keyword allows to list the taxonomical relationships for a selected entity type .\n"
		txt += "==> Usage: ls [%s] tree" % "|".join([x for x in self.LS_OPTS if x in ["classes", "properties", "concepts"]])		
		txt += "\n\nNote: ls is contextual. If you do not pass it any argument, it returns info based on the currently active object.\n"
		self._print(txt)

	def help_download(self):
		txt = "Download an ontology from a remote repository or directory.\n"
		txt += "==> Usage: download [http uri]"		
		self._print(txt)

	def help_visualize(self):
		txt = "Visualize the currenlty selected ontology using an HTML template. Optionally this can be saved as an anonymous GitHub Gist.\n"
		txt += "==> Usage: visualize [gist]" 	
		self._print(txt)

	def help_file(self):
		txt = "Perform some operations on the files in the local repository.\n"
		txt += "==> Usage: file [%s]" % "|".join([x for x in self.FILE_OPTS])		
		self._print(txt)

	def help_serialize(self):
		txt = "Serialize an entity into an RDF flavour.\n"
		txt += "==> Usage: serialize [%s]" % "|".join([x for x in self.SERIALIZE_OPTS])		
		self._print(txt)

	def help_get(self):
		txt = "Finds entities matching a given string pattern.\n"
		txt += "==> Usage: get [%s] <name>" % "|".join([x for x in self.GET_OPTS])		
		self._print(txt)
									
	def help_display(self):
		txt = "Display information about an entity e.g. ontology, class etc..\n"
		txt += "==> Usage: display [%s]" % "|".join([x for x in self.DISPLAY_OPTS])		
		self._print(txt)

	def _help_noontology(self):
		"""starts with underscore so that it doesnt appear with help methods"""
		txt = "No graph selected. Please load a graph first.\n"
		txt += "==> E.g. use the 'ls ontologies' or 'get ontology <name>' commands." 
		self._print(txt)

	def _help_nofiles(self):
		"""starts with underscore so that it doesnt appear with help methods"""
		txt = "No files available in your local repository.\n"
		txt += "==> Use the 'download starter-pack' command to get started." 
		self._print(txt)



	# AUTOCOMPLETE METHODS
	# --------

	def complete_ls(self, text, line, begidx, endidx):
		"""completion for ls command"""
		
		options = self.LS_OPTS

		if not text:
			completions = options
		else:
			completions = [ f
							for f in options
							if f.startswith(text)
							]
		return completions	

	def complete_get(self, text, line, begidx, endidx):
		"""completion for find command"""
		
		options = self.GET_OPTS

		if not text:
			completions = options
		else:
			completions = [ f
							for f in options
							if f.startswith(text)
							]
		return completions	


	def complete_display(self, text, line, begidx, endidx):
		"""completion for display command"""
		
		opts = self.DISPLAY_OPTS
		

		if not text:
			completions = opts
		else:
			completions = [ f
							for f in opts
							if f.startswith(text)
							]
		return completions	
		
	def complete_serialize(self, text, line, begidx, endidx):
		"""completion for serialize command"""
		
		opts = self.SERIALIZE_OPTS

		if not text:
			completions = opts
		else:
			completions = [ f
							for f in opts
							if f.startswith(text)
							]
		return completions	

	def complete_file(self, text, line, begidx, endidx):
		"""completion for file command"""
		
		opts = self.FILE_OPTS

		if not text:
			completions = opts
		else:
			completions = [ f
							for f in opts
							if f.startswith(text)
							]
		return completions	



	
def main():
	""" standalone line script """
	
	print "OntoSPy " + ontospy.VERSION
	
	Shell()._clear_screen()
	print Style.BRIGHT + "** OntoSPy Interactive Ontology Browser " + ontospy.VERSION + " **" + Style.RESET_ALL
	ontospy.get_or_create_home_repo()
	Shell().cmdloop()
	raise SystemExit, 1
		
		

if __name__ == '__main__':
	import sys
	try:
		main()
		sys.exit(0)
	except KeyboardInterrupt, e: # Ctrl-C
		raise e