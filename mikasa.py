# -*- coding: utf-8 -*-

__all__ = [
    "XhpRenderer", 
    "TreeRenderer", 
]

import misaka as m
import houdini as h
import time
import random
import re


class TreeRenderer(m.HtmlRenderer):
    
    def __init__(self, flags=0, nesting_level=0, identifier=""):
        m.HtmlRenderer.__init__(self, flags, nesting_level)
        self.identifier = identifier
        self._section_written = False
        self._application = self._generate_application()
        self._node_level = 0
    
    # own functions
    
    def _generate_id(self):
        return '%08d' % (random.uniform(0, 99999999))
    
    def _generate_application(self):
        a = [chr(v + 0x61) for v in range(26)]
        return "".join((random.choice(a) for i in range(5)))
    
    # misaka related
    
    def list(self, content, is_ordered, is_block):
        return content
    
    def listitem(self, content, is_ordered, is_block):
        return content
    
    def link(self, content, link, title=""):
        link = re.sub("^(./|../)", "", link)
        link = re.sub(".md$", ".xhp", link)
        return """<topic id="{APP}/{ID}/{NAME}">{CONTENT}</topic>\n""".format(
            ID=self.identifier, APP=self._application, CONTENT=content, NAME=link)
    
    def header(self, content, level):
        # todo: multi-section allowed?
        if level == 1 and not self._section_written:
            self._section_written = True
            return """<help_section application="{APP}" id="{ID}" title="{CONTENT}">\n""".format(
                CONTENT=content, ID=self._generate_id(), APP=self._application)
        elif level == 2:
            s = ""
            if self._node_level > 0:
                s = "</node>\n"
            self._node_level += 1
            s += """<node id="{ID}" title="{CONTENT}">\n""".format(
                CONTENT=content, ID=self._generate_id())
            return s
        return ""
    
    def paragraph(self, content):
        return content
    
    def entity(self, text):
        return text
    
    def normal_text(self, text):
        return h.escape_html(text.strip())
    
    def doc_header(self, inline_render):
        return """<?xml version="1.0" encoding="UTF-8"?>
<tree_view version="13-11-2011">\n"""
    
    def doc_footer(self, inline_render):
        s = ""
        if self._node_level > 0:
            while self._node_level:
                self._node_level -= 1
                s += "</node>\n"
        s += """</help_section>
</tree_view>"""
        return s


class XhpRenderer(m.HtmlRenderer):
    """ Rendering XHP file from Markdown. """
    
    def __init__(self, flags=0, nesting_level=0, 
                file_name="", lang="en", identifier="", base_addr="", 
                show_error=False, emphasise_table_header=True, 
                use_dummy_hrule=False):
        m.HtmlRenderer.__init__(self, flags, nesting_level)
        self.file_name = file_name
        self.lang = lang
        self.identifier = identifier
        self.base_addr = base_addr
        self.is_show_error = show_error
        self.emphasise_table_header = emphasise_table_header
        self.use_dummy_hrule = use_dummy_hrule
    
    # own functions
    
    def _get_file_name(self):
        return "/{ID}/{NAME}".format(ID=self.identifier, NAME=self.file_name)
    
    def _get_timestamp(self):
        return time.strftime('%Y-%m-%dT%H:%M:%S')
    
    def _generate_id(self, prefix):
        return '%s_id%08d' % (prefix, random.uniform(0, 99999999))
    
    SIMPLE_TAG_EXP = re.compile("<[^<>]*>", re.M)
    
    def _strip_tags(self, text):
        return h.escape_html(self.SIMPLE_TAG_EXP.sub("", text))
    
    def _parse_template(self, m):
        # templates in {{VALUES}} form
        if not m:
            return ""
        parts = m.group(1).split("|")
        try:
            return getattr(self, "_" + parts[0])(parts)
        except:
            return self._write_template_error(parts)
    
    def _write_template_error(self, parts):
        return "invalid: " + h.escape_html("|".join(parts)) if self.is_show_error else ""
    
    def _OOo(self, parts):
        # {{OOo}} or {{PRODUCTNAME}}
        return "%PRODUCTNAME"
    
    _PRODUCTNAME = _OOo
    
    def _Tip(self, parts):
        # {{Tip|CONTENT}}, {{Caution|CONTENT}} or {{Warning|CONTENT}}
        if len(parts) == 2:
            role = parts[0].lower()
            if role == "caution":
                role = "warning"
            return self.paragraph(h.escape_html(parts[1]), role=role)
        return self._write_template_error(parts)
    
    _Note = _Tip
    _Caution = _Tip
    _Warning = _Tip
    
    def _aHelp(self, parts):
        # {{aHelp|HID|VISIBILITY|CONTENT}}
        if len(parts) == 4:
            return """<ahelp hid="{HID}" visibility="{VISIBILITY}">{CONTENT}</ahelp>""".format(
                HID=h.escape_html(parts[1]), VISIBILITY=("visible" if parts[2] == "visible" else "hidden"), 
                CONTENT=h.escape_html(parts[3]))
        return self._write_template_error(parts)
    
    def _Bookmark(self, parts):
        # {{Bookmark|BRANCH|COMPONENTS|VALUES}}
        # {{Bookmark|BRANCH|VALUES}}
        if len(parts) == 3:
            parts.insert(2, "")
        if len(parts) > 3:
            id = self._generate_id("bk")
            if parts[2]:
                id = id + "_".join([p.strip().lower() for p in parts[2].split(",")])
            values = parts[3].split("||") if len(parts) > 3 else []
            return """<bookmark branch="{BRANCH}" id="{ID}" lang="{LANG}">{VALUES}</bookmark>""".format(
                BRANCH=h.escape_html(parts[1]), ID=id, LANG=self.lang, 
                VALUES="\n".join(["<bookmark_value xml-lang=\"{LANG}\">".format(LANG=self.lang) + h.escape_html(v) + "</bookmark_value>" for v in values]))
        return self._write_template_error(parts)
    
    def _HowToGet(self, parts):
        # {{HowToGet|CONTENT}} or {{RelatedTopics|CONTENT}}
        if len(parts) == 2:
            return """<section id="{ID}" xml-lang="{LANG}">{CONTENT}</section>""".format(
                ID=self._generate_id("sec"), LANG=self.lang, CONTENT=h.escape_html(parts[1]))
        return self._write_template_error(parts)
    
    _RelatedTopics = _HowToGet
    
    def _Variable(self, parts):
        # {{Variable|ID|VISIBILITY|CONTENT}}
        if len(parts) == 4:
            return """<variable id="{ID}" visibility="{VISIBILITY}">{CONTENT}</variable>""".format(
                ID=self._generate_id("var"), VISIBILITY=("visible" if parts[2] == "visible" else "hidden"), 
                CONTENT=h.escape_html(parts[3]))
        return self._write_template_error(parts)
    
    def _Embedvar(self, parts):
        # {{Embedvar|HREF}}
        if len(parts) == 2:
            link = parts[1]
            # todo generate link
            return """<embedvar href="{HREF}" />""".format(HREF=link)
        return self._write_template_error(parts)
    
    # misaka related
    
    def header(self, content, level):
        s = ""
        if level == 1:
            # insert bookmark
            s += """<bookmark branch="index" id="{ID}" xml-lang="{LANG}"><bookmark_value>{CONTENT}</bookmark_value></bookmark>\n""".format(
                ID=self._generate_id("id"), CONTENT=self._strip_tags(content), LANG=self.lang)
        s += """<paragraph id="{ID}" level="{LEVEL}" role="heading" xml-lang="{LANG}">{CONTENT}</paragraph>\n""".format(
            LEVEL=level, ID=self._generate_id("hd"), CONTENT=content, LANG=self.lang)
        return s
    
    def paragraph(self, content, role="paragraph"):
        # role is additional parameter
        return """<paragraph id="{ID}" role="{ROLE}" xml-lang="{LANG}">{CONTENT}</paragraph>\n""".format(
            ID=self._generate_id("par"), ROLE=role, CONTENT=content, LANG=self.lang)
    
    def list(self, content, is_ordered, is_block):
        return """<list type="{TYPE}" {FORMAT}>\n{CONTENT}</list>\n""".format(
            TYPE=("ordered" if is_ordered else "unordered"), 
            FORMAT=("format=\"1\"" if is_ordered else "bullet=\"disc\""), CONTENT=content)
    
    def listitem(self, content, is_ordered, is_block):
        return """<listitem>{CONTENT}</listitem>\n""".format(CONTENT=content.rstrip())
    
    def blockquote(self, content):
        # not supported
        return content
    
    def codespan(self, text):
        return h.escape_html(text)
    
    def emphasis(self, content):
        # italic is invalid
        return "<emph>{CONTENT}</emph>".format(CONTENT=content)
    
    double_emphasis = emphasis
    triple_emphasis = emphasis
    
    def image(self, link, title="", alt=""):
        # todo resolve image location and width/height?
        if link.startswith(self.base_addr):
            link = link[len(self.base_addr):]
            link = "{ID}/{LINK}".format(ID=h.escape_html(self.identifier), LINK=link)
        return """<image id="{ID}" src="{SRC}">{CONTENT}</image>""".format(
            ID=self._generate_id("img"), SRC=link, CONTENT=title)
    
    def link(self, content, link, title=""):
        title = h.escape_html(title)
        if title is None:
            title = ""
        if not re.match("(http://|https://|ftp://|vnd.sun.star.help://)", link):
            link = re.sub("^(./|../)", "", link)
            link = re.sub(".md$", ".xhp", link)
            link = "{ID}/{LINK}".format(ID=h.escape_html(self.identifier), LINK=link)
        return """<link href="{HREF}" name="{NAME}">{CONTENT}</link>""".format(
            HREF=link, NAME=title, CONTENT=content)
    
    def linebreak(self):
        return "<br />"
    
    COMMENT_EXT_EXP = re.compile("<!--\s*\{\{([^\}]*)\}\}\s*-->", re.M)
    
    def raw_html(self, text):
        if text == "<br />":
            return self.linebreak()
        if self.is_show_error:
            return "-- raw html is invalid --"
        return ""
    
    def blockhtml(self, text):
        m = self.COMMENT_EXT_EXP.match(text)
        if m:
            return self._parse_template(m)
        return ""
    
    def entity(self, text):
        return text
    
    def normal_text(self, text):
        return h.escape_html(text)
    
    def hrule(self):
        if self.use_dummy_hrule:
            return self.paragraph("--------", role="paragraph")
        return ""
    
    def doc_header(self, inline_render):
        # todo meta/history
        return """<?xml version="1.0" encoding="UTF-8"?>
<helpdocument version="1.0">
 <meta>
  <topic id="topic_" indexer="include">
  <title id="tit" xml-lang="{LANG}"></title>
  <filename>{FILENAME}</filename>
 </topic>
 </meta>
<body>\n""".format(
        LANG=self.lang, CREATED="", EDITED="", 
        FILENAME=h.escape_html(self._get_file_name()))
    
    def doc_footer(self, inline_render):
        return """\n</body></helpdocument>"""
    
    # extensions
    
    def table(self, content):
        return """<table id="{ID}">\n{CONTENT}</table>\n""".format(
            ID=self._generate_id("tab"), CONTENT=content)
    
    def table_header(self, content):
        return content
    
    def table_body(self, content):
        return content
    
    def table_row(self, content):
        return """<tablerow>{CONTENT}</tablerow>\n""".format(
            CONTENT=content)
    
    def table_cell(self, content, align, is_header):
        if is_header and self.emphasise_table_header:
            content = "<emph>{CONTENT}</emph>".format(CONTENT=content)
        return """<tablecell>{CONTENT}</tablecell>""".format(
                CONTENT=content)
    
    def blockcode(self, text, lang=""):
        return self.paragraph("<br />".join(h.escape_html(text).split("\n")), role="code")
    
    def footnotes(self, content):
        pass # not supported
    
    def footnote_def(self, content, num):
        pass # not supported
    
    def footntoe_ref(self, num):
        pass # not supported
    
    def autolink(self, link, is_email):
        url = h.escape_html(link)
        return """<link href="{URL}">{URL}</link>""".format(URL=url)
    
    def strikethrough(self, content):
        # not supported
        return "~~" + content + "~~"
    
    def underline(self, content):
        # not supported
        return content
    
    def highlight(self, content):
        # not supported?
        return content
    
    def quote(self, content):
        # todo
        #return self.paragraph(content)
        return "&quot;" + content + "&quot;"
    
    def superscript(self, content):
        # not supported
        return content
    
    def math(self, text, displaymode):
        # not supported
        return h.escape_html(text)


def main():
    extensions=[
        "tables", "fenced-code", "footnotes", "autolink", "strikethrough", "underline", 
        "highlight", "quote", "superscript", "no-intra-emphasis", "space-headers", 
        "disable-indented-code",]
    from pathlib import Path
    import argparse
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-s", "--src", default="./data", required=False, 
            help="Source directorie which contains LANG/*.md")
    parser.add_argument("-d", "--dest", default="./help", required=False, 
            help="Destination directory is used to store generated files")
    parser.add_argument("-i", "--id", required=True, 
            help="Extension identifier")
    parser.add_argument("-b", "--base", default="", required=False, 
            help="Base URL for internal relative link for images")
    parser.add_argument("-l", "--langs", default="", required=False, 
            help="Specify languages to be converted, multiple language codes can be joined with comma")
    
    args = parser.parse_args()
    
    identifier = args.id
    languages = args.langs.split(",") if args.langs else []
    src = Path(args.src).resolve()
    dest = Path(args.dest).resolve()
    
    if not src.is_dir():
        raise Exception("Specify directory to src")
    if not src.exists():
        src.mkdir()
    if not dest.is_dir():
        raise Exception("Specify directory to dest")
    
    renderer = XhpRenderer(identifier=identifier, base_addr=args.base)
    md = m.Markdown(renderer, extensions)
    
    def render(base, path, lang, non_tree=False):
        dest_path = path.with_suffix(".xhp" if non_tree else ".tree")
        relative_path = dest_path.relative_to(base)
        relative_path = Path(*relative_path.parts[1:])
        
        if non_tree:
            dest_path = dest / lang / identifier / relative_path
        else:
            dest_path = dest / lang / relative_path
        if not dest_path.parent.exists():
            dest_path.parent.mkdir(parents=True)#, exist_ok=True)
        
        with path.open(encoding="utf-8") as f:
            content = f.read()
        if non_tree:
            renderer.file_name = relative_path
            renderer.lang = lang
            result = md(content)
        else:
            result = m.Markdown(TreeRenderer(identifier=identifier))(content)
        
        with dest_path.open(mode="w", encoding="utf-8") as f:
            f.write(result)
    
    def parse_dir(base, dir_path, lang):
        for path in dir_path.iterdir():
            if path.is_dir():
                parse_dir(base, path, lang)
            elif path.suffix == ".md":
                render(base, path, lang, non_tree=(path.name != "help.md"))
    
    is_parse_all = len(languages) == 0
    
    for lang_dir in src.iterdir():
        if lang_dir.is_dir():
            lang = lang_dir.relative_to(src)
            if is_parse_all or str(lang) in languages:
                parse_dir(src, lang_dir, str(lang))


if __name__ == "__main__":
    main()
