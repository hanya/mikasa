
Mikasa
======

Mikasa is Misaka based Markdown to XHP convertor written in Python. 
The parser is Hoedown called through CFFI by Misaka.

* Misaka: https://github.com/FSX/misaka
* Hoedown: https://github.com/hoedown/hoedown


## How to use
Requires Python 3.4 or later.

You need Misaka installed on your Python environment.

```
(mikasa)#  python mikasa.py -h
usage: mikasa.py [-h] [-s SRC] [-d DEST] -i ID [-b BASE] [-l LANGS]

optional arguments:
  -h, --help            show this help message and exit
  -s SRC, --src SRC     Source directorie which contains LANG/*.md
  -d DEST, --dest DEST  Destination directory is used to store generated files
  -i ID, --id ID        Extension identifier
  -b BASE, --base BASE  Base URL for internal relative link for images
  -l LANGS, --langs LANGS
                        Specify languages to be converted, multiple language
                        codes can be joined with comma
```


## About XHP file format
XHP file format is help file for OpenOffice. It is converted into HTML while 
showing in the help viewer of the office. The text data must be encoded in UTF-8.

If you want to provider online help as part of your extension of the office, 
you need provide them in XHP format. But it is hard to write the file by hand. 
This tool allows you to write your help files in Markdown.

See the developer's guide for more detail of the XHP file format and 
directory structure in your extension package.

Developer's Guide: https://wiki.openoffice.org/wiki/Documentation/DevGuide/Extensions/Help_Content


## Directory structure
The files having *.md file extensions only are parsed. 
Conent of your help files should be stored in the directories.

```
Working directory
|
|- data (SRC directory, can be specified by -s/--src)
   |- LANG (ISO language code, can be specified by -l/--langs)
      |- file1.md
      |- file2.md
      |- help.md (This file contains help.tree data, see below)
```

You can put Markdown files into sub directories. 
These files are converted into the following structure.

```
Working directory
|
|- help (DEST direcotry, can be choosen by -d/--dest)
   |- LANG (ISO code, see -l/--langs)
   |  |- ID (Extension identifier, see extension creation)
   |     |- file1.md
   |     |- file2.md
   |- help.tree
```

With the above structure, you can specify your help contents with the 
following entry in META-INF/manifest.xml file.

```
 <manifest:file-entry manifest:full-path="help" 
 manifest:media-type="application/vnd.sun.star.help"/>
```

In the above, manifest:full-path="help" specifies the help directory. 
Change it according to your file structure if you store your files 
into different place.


## Valid Markdown syntax
Any other syntax are not supported because there is no related 
format in XHP format.

|Syntax|Description|
|----|----|
|Heading 1|Used as title of the page, start your page with this|
|other headings|Converted into headings|
|emphasise|Bold only, no italic supported|
|link|Converted into internal or external link|
|table|into table|
|autolink|URL or something will be linked|
|code|pre like but no indentation support|
|list|supported|
|manual br|supported|
|image|to do|


## Template extension
Some important elements can be generated by templates. 

You can add tip, caution or warning section with the following way.

```
<!-- {{Tip|CONTENT}} -->
<!-- {{Caution|CONTENT}} -->
<!-- {{Warning|CONTENT}} -->
```

CONTENT is the text which you want to embed. Warning is converted into 
the caution because of the unsupport.

Bookmark generates entries for help viewer. If you want to add your 
own entries into Index list of the viewer, define with this template.

```
<!-- {{Bookmark|BRANCH|COMPONENTS|VALUES}} -->
<!-- {{Bookmark|BRANCH|VALUES}} -->
```

BRANCH can be "index" or the way of "hid/...". If you specify "index", the 
VALUES are shown in Index list of the help viewer. For "index" branch, 
you can add your entries under specified parent with "parent/child" way 
separated with "/" character.

COMPONENTS can be omitted and it specifies the category which your entries 
are shown. It is comma separated value, each value is one of 
sbasic, scalc, schart, sdatabase, sdraw, simpress, smath, swriter.

VALUES is the title of your entry which is shown as the entry. You 
can specify multiple entries in "||" separated.

Detailed tooltip of your user interface can be defined with: 

```
<!-- {{aHelp|HID|VISIBILITY|CONTENT}} -->
```

HID is the help ID of your UI control like: mytools.Mri:edit_in. 
VISIBILITY is one of hidden or visible. If VISIBILITY is visible, 
the CONTENT is shown on your help file also. 

You have to put Bookmark having related BRANCH on the same page 
if you have aHelp. Insert "hid/" before your help ID for the 
BRANCH of your Bookmark entry.

Here is an example contains both aHelp and Bookmark.
```
<!-- {{Bookmark|hid/mytools.Mri:edit_in|Implemenation Name Field}} -->

<!-- {{aHelp|mytools.Mri:edit_in|hidden|Implementation name of the current target}} -->
```

You can show how to get section with the following: 

```
<!-- {{HowToGet|CONTENT}} -->
<!-- {{RelatedTopics|CONTENT}} -->
```

Some variable is used in another places can be defined. And can be 
embeded with the Embedvar template.

```
<!-- {{Variable|ID|VISIBILITY|CONTENT}} -->
<!-- {{Embedvar|HREF}} -->
```

HREF is written in PageName#ID.


## help.md file
Tree structure is shown in the side window of the help viewer. 
It can be defined by help.md which is converted into help.tree file.

Here is an example: 

```
# MRI
* [MRI Documentation](./README.md)

## All Pages
* [Index Page](./README.md)
```

First level 1 heading specifies top name of the your tree. 
If you put some link on the file, they will be converted into entries. 
In the above example, the list syntax is ignored but they are useful to 
see on some Markdown viewer.

The another heading having level 2 genarates child node in your tree. 
You can put some links to your pages in this element also.


## LICENSE
The MIT License, see LICENSE.
