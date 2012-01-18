/* ***** BEGIN LICENSE BLOCK *****
* Version: MPL 1.1/GPL 2.0/LGPL 2.1
*
* The contents of this file are subject to the Mozilla Public License Version
* 1.1 (the "License"); you may not use this file except in compliance with
* the License. You may obtain a copy of the License at
* http://www.mozilla.org/MPL/
*
* Software distributed under the License is distributed on an "AS IS" basis,
* WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
* for the specific language governing rights and limitations under the
* License.
*
* The Original Code is Ajax.org Code Editor (ACE).
*
* The Initial Developer of the Original Code is
* Ajax.org B.V.
* Portions created by the Initial Developer are Copyright (C) 2010
* the Initial Developer. All Rights Reserved.
*
* Contributor(s):
*      Fabian Jakobs <fabian AT ajax DOT org>
*      Colin Gourlay <colin DOT j DOT gourlay AT gmail DOT com>
*
* Alternatively, the contents of this file may be used under the terms of
* either the GNU General Public License Version 2 or later (the "GPL"), or
* the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
* in which case the provisions of the GPL or the LGPL are applicable instead
* of those above. If you wish to allow use of your version of this file only
* under the terms of either the GPL or the LGPL, and not to allow others to
* use your version of this file under the terms of the MPL, indicate your
* decision by deleting the provisions above and replace them with the notice
* and other provisions required by the GPL or the LGPL. If you do not delete
* the provisions above, a recipient may use your version of this file under
* the terms of any one of the MPL, the GPL or the LGPL.
*
* ***** END LICENSE BLOCK ***** */
define('ace/mode/buildout', function(require, exports, module) {

    var oop = require("ace/lib/oop");
    var TextMode = require("ace/mode/text").Mode;
    var Tokenizer = require("ace/tokenizer").Tokenizer;
    var BuildoutHighlightRules = require("ace/mode/buildout_highlight_rules").BuildoutHighlightRules;
    var Range = require("ace/range").Range;

    var Mode = function() {
        this.$tokenizer = new Tokenizer(new BuildoutHighlightRules().getRules());
    };
    oop.inherits(Mode, TextMode);

    (function() {

        this.toggleCommentLines = function(state, doc, startRow, endRow) {
            var outdent = true;
            var re = /^(\s*)#/;

            for (var i=startRow; i<= endRow; i++) {
                if (!re.test(doc.getLine(i))) {
                    outdent = false;
                    break;
                }
            }

            if (outdent) {
                var deleteRange = new Range(0, 0, 0, 0);
                for (var i=startRow; i<= endRow; i++)
                {
                    var line = doc.getLine(i);
                    var m = line.match(re);
                    deleteRange.start.row = i;
                    deleteRange.end.row = i;
                    deleteRange.end.column = m[0].length;
                    doc.replace(deleteRange, m[1]);
                }
            }
            else {
                doc.indentRows(startRow, endRow, "//");
            }
        };

        this.getNextLineIndent = function(state, line, tab) {
            var indent = this.$getIndent(line);

            var tokenizedLine = this.$tokenizer.getLineTokens(line, state);
            var tokens = tokenizedLine.tokens;
            var endState = tokenizedLine.state;

            if (tokens.length && tokens[tokens.length-1].type == "comment") {
                return indent;
            }

            if (state == "start") {
                var intern_match = line.match(/^.+=\s*$/);
                if (intern_match) {
                    indent += tab;
                }                
            }

            return indent;
        };
        var outdents = {
            "\r\n": 1,
            "\r": 1,
            "\n": 1
        };

        this.checkOutdent = function(state, line, input) {
            if (input !== "\r\n" && input !== "\r" && input !== "\n")
                return false;

            var tokens = this.$tokenizer.getLineTokens(line.trim(), state).tokens;
        
            if (!tokens)
                return false;
        
            // ignore trailing comments
            do {
                var last = tokens.pop();
            } while (last && (last.type == "comment" || (last.type == "text" && last.value.match(/^\s+$/))));
        
            if (!last)
                return false;
            return (last.type == "keyword" && outdents[last.value]);
        };

        this.autoOutdent = function(state, doc, row) {
            // outdenting in python is slightly different because it always applies
            // to the next line and only of a new line is inserted
        
            row += 1;
            var indent = this.$getIndent(doc.getLine(row));
            var tab = doc.getTabString();
            if (indent.slice(-tab.length) == tab)
                doc.remove(new Range(row, indent.length-tab.length, row, indent.length));
        };

    }).call(Mode.prototype);

    exports.Mode = Mode;
});

define('ace/mode/buildout_highlight_rules', function(require, exports, module) {

    var oop = require("ace/lib/oop");
    var lang = require("ace/lib/lang");
    var unicode = require("ace/unicode");
    var TextHighlightRules = require("ace/mode/text_highlight_rules").TextHighlightRules;

    var BuildoutHighlightRules = function() {

        var keywords = lang.arrayToMap(
            ("parts|develop|versions|extends|depends|find-links|allow-hosts").split("|")
            );
        var buildinConstants = lang.arrayToMap(
            ("null|true|false").split("|")
            );        
        var strPre = "(?:r|u|ur|R|U|UR|Ur|uR)?";
        var decimalInteger = "(?:(?:[1-9]\\d*)|(?:0))";
        var octInteger = "(?:0[oO]?[0-7]+)";
        var hexInteger = "(?:0[xX][\\dA-Fa-f]+)";
        var binInteger = "(?:0[bB][01]+)";
        var integer = "(?:" + decimalInteger + "|" + octInteger + "|" + hexInteger + "|" + binInteger + ")";

        var exponent = "(?:[eE][+-]?\\d+)";
        var fraction = "(?:\\.\\d+)";
        var intPart = "(?:\\d+)";
        var pointFloat = "(?:(?:" + intPart + "?" + fraction + ")|(?:" + intPart + "\\.))";
        var exponentFloat = "(?:(?:" + pointFloat + "|" +  intPart + ")" + exponent + ")";
        var floatNumber = "(?:" + exponentFloat + "|" + pointFloat + ")";
    
        // regexp must not have capturing parentheses. Use (?:) instead.
        // regexps are ordered -> the first match is used

        this.$rules = {
            "start" : [                
            {
                token : "keyword", // begin buildout part
                regex : "^\\[[a-zA-Z-_][a-zA-Z0-9-_]*\\]"
            }, {
                token : "comment",
                regex : "#.*$"
            }, {
                token : "string",           // """ string
                regex : strPre + '"{3}(?:[^\\\\]|\\\\.)*?"{3}'
            }, {
                token : "string",           // multi line """ string start
                merge : true,
                regex : strPre + '"{3}.*$',
                next : "qqstring"
            }, {
                token : "string",           // " string
                regex : strPre + '"(?:[^\\\\]|\\\\.)*?"'
            }, {
                token : "string",           // ''' string
                regex : strPre + "'{3}(?:[^\\\\]|\\\\.)*?'{3}"
            }, {
                token : "string",           // multi line ''' string start
                merge : true,
                regex : strPre + "'{3}.*$",
                next : "qstring"
            }, {
                token : "string",           // ' string
                regex : strPre + "'(?:[^\\\\]|\\\\.)*?'"
            }, {
                token : "constant.numeric", // imaginary
                regex : "(?:" + floatNumber + "|\\d+)[jJ]\\b"
            }, {
                token : "constant.numeric", // float
                regex : floatNumber
            }, {
                token : "constant.numeric", // long integer
                regex : integer + "[lL]\\b"
            }, {
                token : "constant.numeric", // integer
                regex : integer + "\\b"
            },{
                token: "support.function",
                regex: "^[\\w\\d-_\\.]+\\s*\\+?="
            }, {
                token : function(value) {
                    if (keywords.hasOwnProperty(value.toLowerCase())) {
                        return "support.function";
                    }
                    else if (buildinConstants.hasOwnProperty(value.toLowerCase())) {
                        return "support.constant";
                    }
                    else {
                        return "text";
                    }
                },
                regex : "\\-?[a-zA-Z_][a-zA-Z0-9_\\-]*"
            }, {
                token : "variable",
                regex : "\\$\\{[a-zA-Z-_:\\.][a-zA-Z0-9-_:\\.]*\\}"
            }, {
                token: "string",
                regex: '\\s(?:ht|f)tps?:\\/\\/[a-z0-9-\\._:]+\\.[a-z]{2,4}\\/?(?:[^\\s<>\\#%"\\,\\{\\}\\\\|\\\\\\^\\[\\]`]+)?\\s*$'
            }, {
                token : "constant.language",
                regex : "^<=\\s*[\\w\\d-_]+"
            }
            
            ],
            // regular expressions are only allowed after certain tokens. This
            // makes sure we don't mix up regexps with the divison operator
            "regex_allowed": [
            {
                token : "comment", // multi line comment
                merge : true,
                regex : "\\/\\*",
                next : "comment_regex_allowed"
            }, {
                token : "comment",
                regex : "\\/\\/.*$"
            }, {
                token: "string.regexp",
                regex: "\\/(?:(?:\\[(?:\\\\]|[^\\]])+\\])"
                + "|(?:\\\\/|[^\\]/]))*" 
                + "[/]\\w*",
                next: "start"
            }, {
                token : "text",
                regex : "\\s+"
            }, {
                // immediately return to the start mode without matching
                // anything
                token: "empty", 
                regex: "",
                next: "start"
            }
            ],
            "comment_regex_allowed" : [
            {
                token : "comment", // closing comment
                regex : ".*?\\*\\/",
                merge : true,
                next : "regex_allowed"
            }, {
                token : "comment", // comment spanning whole line
                merge : true,
                regex : ".+"
            }
            ],
            "comment" : [
            {
                token : "comment", // closing comment
                regex : ".*?\\*\\/",
                merge : true,
                next : "start"
            }, {
                token : "comment", // comment spanning whole line
                merge : true,
                regex : ".+"
            }
            ],
            "qqstring" : [
            {
                token : "string",
                regex : '(?:(?:\\\\.)|(?:[^"\\\\]))*?"',
                next : "start"
            }, {
                token : "string",
                merge : true,
                regex : '.+'
            }
            ],
            "qstring" : [
            {
                token : "string",
                regex : "(?:(?:\\\\.)|(?:[^'\\\\]))*?'",
                next : "start"
            }, {
                token : "string",
                merge : true,
                regex : '.+'
            }
            ]
        };
    };

    oop.inherits(BuildoutHighlightRules, TextHighlightRules);

    exports.BuildoutHighlightRules = BuildoutHighlightRules;
});

