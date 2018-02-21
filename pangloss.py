#!/usr/bin/env python

# pangloss
# Language detector for files.
# Copyright (C) 2016-2018 by Emery Berger <http://emeryberger.com>
#
# This language detector works by examining source contents and
# only uses file extensions as a hint. Based on a learned model
# from corpora of programs.
#
# Usage:
#   pangloss filename.ext

# Currently supports the following languages:

classes = ["C++", "JavaScript", "Java", "C", "Ruby", "Perl", "TypeScript", "Python", "Scala", "PHP", "Objective-C"]

# Each extension corresponds to the classifier above.
# We incorporate extension info as a weak prior, below.
extensions = [[".cpp", ".hpp", ".hh", ".cc", ".cxx", ".hxx", ".C"],
              [".js"],
              [".java"],
              [".c",".h"],
              [".rb"],
              [".pl",".pm"],
              [".ts"],
              [".py"],
              [".scala"],
              [".php"],
              [".m"]]

extensionPrior = 1.1 # 10% more likely if it has the given suffix

import os
import sys
import csv
import math

def help():
    print "pangloss determines the programming language a file is written in."
    print "Usage: pangloss { filename [--ext=XYZ] }"
    print("       The --ext argument can override the physical extension of the file")
    print("Alternatively, pangloss can run in a batch mode, where --batch=XYZ argument")
    print("contains list of files, possibly followed by their extension hints")
    sys.exit(1)

input = []
if (len(sys.argv) < 2):
    help();
if (sys.argv[1].startswith("--batch=")):
    # batch mode
    if (len(sys.argv) > 2):
        help()
    with open(sys.argv[1][8:]) as f:
        for line in f:
            x = line.split(",")
            if (len(x) == 1):
                len.append(os.path.splitext(x[0])[1])
            input.append((x[0], x[1]))
else:
    i = 1
    while (i < len(sys.argv)):
        fname = sys.argv[i]
        i += 1
        if (i < len(sys.argv) and sys.argv[i].startswith("--ext=")):
            ext = sys.argv[i][6:]
            i += 1
        else:
            ext = os.path.splitext(fname)[1]
        input.append((fname, ext))    
            
def words(fileobj):
    for line in fileobj:
        for word in line.split():
            yield word

objc = { '=' : 32651 ,  '{' : 29226 ,  '}' : 29057 ,  'if' : 16587 ,  '*' : 14653 ,  '==' : 10984 ,  'return' : 9412 ,  '-' : 8849 ,  '*/' : 7050 ,  '/*' : 5022 ,  '[self' : 4759 ,  'of' : 4623 ,  'else' : 4471 ,  '!=' : 3900 ,  'for' : 3665 ,  '//' : 3092 ,  '#import' : 2980 ,  '0)' : 2974 ,  '0;' : 2901 ,  '(void)' : 2879 ,  '&&' : 2856 ,  'in' : 2699 ,  '+' : 2679 ,  'NSString' : 2527 ,  'nil;' : 2468 ,  'nil)' : 2287 ,  '/**' : 2055 ,  'int' : 2017 ,  'unsigned' : 2012 ,  'static' : 1965 ,  'case' : 1930 ,  '<' : 1814 ,  '>' : 1795 ,  'NO;' : 1699 ,  'with' : 1663 ,  '(id)' : 1658 ,  'while' : 1603 ,  '#endif' : 1599 ,  'this' : 1523 ,  'char' : 1485 ,  'break;' : 1464 ,  'not' : 1412 ,  'as' : 1336 ,  'YES;' : 1327 ,  'alloc]' : 1311 ,  'This' : 1301 ,  '@end' : 1264 ,  '||' : 1251 ,  'or' : 1214 ,  '0' : 1200 ,  ':' : 1175 ,  '#if' : 1161 ,  'c' : 1124 ,  'const' : 1091 ,  'nil' : 1090 ,  'isEqual:' : 1086 ,  '#define' : 1075 ,  'length:' : 1062 ,  'YES)' : 1059 ,  'void' : 1058 ,  'BOOL' : 1029 ,  'id' : 999 ,  'forKey:' : 919 ,  'format:' : 917 ,  'data' : 913 ,  'have' : 882 ,  'raise:' : 876 ,  'on' : 871 ,  'file' : 870 ,  'i' : 846 ,  'new];' : 831 ,  'If' : 822 ,  'NO)' : 809 ,  '#include' : 802 ,  '*)' : 795 ,  '...' : 788 ,  'return;' : 782 ,  '1' : 771 ,  'method' : 750 ,  '/>' : 747 ,  '(BOOL)' : 743 ,  'string' : 738 ,  '[s' : 737 ,  '0,' : 732 }

php = { '=' : 941422 ,  '{' : 765160 ,  '=>' : 763594 ,  '}' : 762186 ,  'function' : 345522 ,  'public' : 290964 ,  'if' : 259775 ,  'return' : 222685 ,  'new' : 130823 ,  '.' : 123430 ,  'use' : 101998 ,  ');' : 80648 ,  'array(' : 71631 ,  '<?php' : 62340 ,  '),' : 60995 ,  'as' : 60582 ,  'class' : 57626 ,  'else' : 50966 ,  "'0'," : 50585 ,  'foreach' : 42805 ,  '&&' : 42508 ,  'extends' : 42496 ,  'print' : 42073 ,  '[' : 41022 ,  'private' : 40432 ,  "''," : 37404 ,  '==' : 35880 ,  '===' : 34708 ,  'null,' : 33399 ,  ')' : 32729 ,  'array' : 32018 ,  'throw' : 29855 ,  "'id'" : 28604 ,  "'," : 28457 ,  "'1'," : 28078 ,  'array();' : 28040 ,  'case' : 27443 ,  "'" : 26779 ,  '(' : 25320 ,  ':' : 25197 ,  'false;' : 24819 ,  '.=' : 24629 ,  'const' : 24575 ,  '?' : 23339 ,  '||' : 22741 ,  '0,' : 22121 ,  '[],' : 21662 ,  'true,' : 21202 ,  '],' : 20200 ,  'break;' : 19983 ,  'true;' : 19853 ,  '!==' : 19801 ,  'null)' : 19613 ,  'not' : 18855 ,  '0;' : 18660 ,  'null;' : 18267 ,  'static' : 18198 ,  '"' : 17364 ,  '-' : 17316 ,  'false,' : 16309 ,  '0)' : 15346 ,  '+' : 15225 ,  'for' : 14920 ,  '$this;' : 14082 ,  '1,' : 13992 ,  '>' : 13971 ,  "'';" : 13959 ,  'echo' : 13573 ,  '<' : 13100 ,  '$result' : 12622 ,  'global' : 12038 ,  '$sql.=' : 11874 ,  'false);' : 11788 ,  '!=' : 11631 ,  'in' : 11494 ,  '];' : 11216 ,  'AND' : 11149 ,  'of' : 11131 ,  '(!' : 10921 ,  'elseif' : 10771 ,  '*' : 10723 ,  "'type'" : 10596 ,  '1;' : 10473 ,  "'16'," : 9385 ,  'array(),' : 9335 ,  'false)' : 9299 ,  ']' : 9116 ,  "'body'," : 8947 ,  '$data' : 8706 ,  '[];' : 8635 ,  '0' : 8465 ,  'catch' : 8097 ,  'false' : 7932 ,  "'187'," : 7913 }


python = { '=' : 127029 ,  '#' : 75374 ,  'def' : 39952 ,  'the' : 37945 ,  'if' : 32369 ,  'in' : 22803 ,  'return' : 20984 ,  'a' : 20375 ,  'is' : 19248 ,  'for' : 18792 ,  'to' : 17378 ,  '->' : 16634 ,  'of' : 13981 ,  'and' : 13727 ,  'not' : 12204 ,  'import' : 11129 ,  'class' : 10772 ,  'LETTER' : 10544 ,  '+' : 10253 ,  '==' : 10017 ,  "'" : 9692 ,  'LATIN' : 7854 ,  'from' : 7832 ,  '"""' : 7749 ,  'with' : 7340 ,  'be' : 7093 ,  'else:' : 6495 ,  'or' : 6469 ,  '%' : 6417 ,  'None,' : 6384 ,  '1' : 6244 ,  'as' : 6021 ,  ':' : 5902 ,  'that' : 5860 ,  'try:' : 5660 ,  'SMALL' : 5169 ,  'raise' : 5036 ,  'print' : 4991 ,  '-' : 4809 ,  'CAPITAL' : 4679 ,  'pass' : 4628 ,  'this' : 4487 ,  'None' : 4392 ,  'except' : 4289 ,  '0' : 4265 ,  'an' : 4237 ,  'are' : 4200 ,  '>>>' : 3819 ,  'The' : 3798 ,  'it' : 3781 ,  'by' : 3751 ,  'WITH' : 3750 ,  'file' : 3560 ,  'on' : 3404 ,  'name' : 3375 ,  '*' : 3287 ,  'i' : 3142 ,  'x' : 2965 ,  'None:' : 2896 ,  '[]' : 2855 ,  'line' : 2841 ,  'elif' : 2808 ,  'which' : 2555 ,  's' : 2517 ,  'This' : 2507 ,  'test' : 2499 ,  '2' : 2392 ,  'value' : 2364 ,  'c' : 2350 ,  'will' : 2284 ,  'we' : 2272 ,  '"' : 2249 ,  '|' : 2246 ,  'b' : 2210 ,  'should' : 2208 ,  'If' : 2198 ,  '...' : 2189 ,  "'\\n'" : 2140 ,  'can' : 2139 ,  '>' : 2100 ,  '!=' : 2091 ,  '<' : 2076 ,  'all' : 2048 ,  'string' : 2045 ,  '0,' : 2041 ,  'data' : 2023 ,  '1,' : 2018 ,  'module' : 1982 ,  'result' : 1969 ,  '{' : 1924 ,  'list' : 1908 ,  'A' : 1854 ,  'while' : 1845 ,  'object' : 1830 ,  '0)' : 1824 ,  '1)' : 1820 ,  '}' : 1808 ,  'have' : 1788 ,  '\\' : 1727 ,  'when' : 1721 }

scala = { '=' : 187433 ,  '*' : 124068 ,  '{' : 112505 ,  '}' : 106920 ,  'val' : 81495 ,  'def' : 79992 ,  '=>' : 51929 ,  '//' : 51356 ,  'case' : 35328 ,  'of' : 31812 ,  '*/' : 31146 ,  'new' : 30808 ,  'if' : 28925 ,  'import' : 24915 ,  '/**' : 24412 ,  'for' : 22660 ,  'in' : 21795 ,  'with' : 20957 ,  '+' : 20565 ,  'this' : 20430 ,  'class' : 19228 ,  'extends' : 18429 ,  'override' : 15929 ,  '==' : 14181 ,  'else' : 13235 ,  '|' : 12933 ,  'object' : 12326 ,  'or' : 12106 ,  'Int' : 11192 ,  'not' : 10906 ,  'private' : 10787 ,  'under' : 10110 ,  'type' : 9215 ,  'file' : 9155 ,  '0' : 8628 ,  'var' : 8493 ,  '===' : 8462 ,  '"' : 8303 ,  'trait' : 8160 ,  '/*' : 8063 ,  'match' : 7772 ,  'Unit' : 7678 ,  '-' : 7563 ,  'on' : 7487 ,  'License' : 7369 ,  '::' : 7366 ,  '_' : 7058 ,  '@param' : 6800 ,  '&&' : 6774 ,  'package' : 6639 ,  'as' : 6616 ,  '1' : 6597 ,  '**' : 6342 ,  ';' : 6289 ,  '/' : 6246 ,  'may' : 6224 ,  'A' : 6192 ,  'See' : 5566 ,  '->' : 5153 ,  'should' : 5093 ,  'Int,' : 5052 ,  'You' : 5000 ,  'License.' : 4932 ,  'Apache' : 4915 ,  'value' : 4841 ,  'at' : 4791 ,  'x' : 4779 ,  'use' : 4706 ,  'Boolean' : 4696 ,  '+=' : 4688 ,  'one' : 4615 ,  'This' : 4591 ,  'String,' : 4418 ,  'null' : 4304 ,  'String' : 4204 ,  '!=' : 4201 ,  'all' : 4170 ,  'final' : 3906 ,  'more' : 3853 ,  '<-' : 3842 ,  '0)' : 3781 ,  '<' : 3754 ,  'Test' : 3708 ,  '1)' : 3675 ,  ')' : 3662 }


javascript = { '=' : 97582 ,  '{' : 71715 ,  '}' : 42792 ,  'var' : 40475 ,  '*' : 36627 ,  'if' : 30302 ,  '//' : 29291 ,  'return' : 22334 ,  'function' : 21499 ,  'the' : 17250 ,  '+' : 14450 ,  '===' : 11115 ,  'to' : 10506 ,  '});' : 9570 ,  'a' : 8828 ,  '};' : 8479 ,  '&&' : 8176 ,  'new' : 7205 ,  'is' : 6891 ,  'of' : 6867 ,  '||' : 6692 ,  'else' : 6457 ,  'for' : 6451 ,  '},' : 6407 ,  '*/' : 6166 ,  ':' : 5310 ,  '@param' : 5013 ,  '/**' : 4877 ,  'The' : 4650 ,  'in' : 4594 ,  '})' : 4373 ,  'and' : 4365 ,  '0;' : 4290 ,  'i' : 4269 ,  '-' : 4245 ,  '<' : 4209 ,  '!==' : 4051 ,  '?' : 4020 ,  ',' : 3543 ,  'function()' : 3530 ,  'module.exports' : 3251 ,  '+=' : 3149 ,  'not' : 3115 ,  '()' : 3084 ,  'case' : 3009 ,  'const' : 3005 ,  'that' : 2973 ,  'be' : 2962 ,  "'use" : 2945 ,  "strict';" : 2860 ,  'false;' : 2770 ,  '@returns' : 2626 ,  "'" : 2622 ,  'throw' : 2524 ,  'with' : 2520 ,  'true;' : 2481 ,  'an' : 2445 ,  'value' : 2427 ,  'this' : 2408 ,  '0,' : 2383 ,  'node' : 2349 ,  'or' : 2318 ,  '=>' : 2130 ,  'true' : 2101 ,  '0)' : 2059 ,  '==' : 1971 ,  'as' : 1863 ,  '>' : 1819 ,  'it' : 1797 ,  '(var' : 1794 ,  'false' : 1776 ,  '[' : 1738 ,  'are' : 1717 ,  'on' : 1701 ,  'object' : 1684 ,  '(typeof' : 1680 ,  'result' : 1642 ,  'from' : 1640 ,  'Returns' : 1549 ,  'null;' : 1518 ,  'we' : 1495 ,  'return;' : 1429 ,  'array' : 1412 ,  '0' : 1411 ,  '&' : 1388 ,  'true,' : 1381 ,  'cb)' : 1379 ,  'should' : 1346 ,  '[];' : 1297 ,  'path' : 1289 ,  'false,' : 1286 ,  'while' : 1273 ,  '(t)' : 1265 ,  'by' : 1256 ,  'options' : 1252 ,  'assert' : 1250 ,  'type:' : 1234 ,  'i++)' : 1224 ,  'null' : 1221 ,  'break;' : 1206 }

cplusplus = { '//' : 199606 ,  '=' : 124262 ,  '{' : 111007 ,  '}' : 88909 ,  'if' : 64362 ,  'the' : 51906 ,  'return' : 43217 ,  'void' : 37224 ,  'a' : 30266 ,  'to' : 27065 ,  'for' : 26911 ,  'const' : 24195 ,  'of' : 23185 ,  'case' : 22367 ,  'int' : 22043 ,  'is' : 21940 ,  '///' : 21211 ,  'CHECK:' : 21120 ,  '};' : 19450 ,  'struct' : 18760 ,  '<<' : 17860 ,  ':' : 16274 ,  '&&' : 16014 ,  '==' : 14989 ,  'in' : 12586 ,  '-' : 12579 ,  'bool' : 12567 ,  '|' : 11372 ,  '#pragma' : 11244 ,  'omp' : 11176 ,  'class' : 10844 ,  'be' : 10631 ,  'else' : 10245 ,  'and' : 9703 ,  'we' : 9492 ,  'template' : 9186 ,  'this' : 9093 ,  'not' : 8940 ,  '0;' : 8822 ,  'type' : 8759 ,  'that' : 8609 ,  'i' : 8592 ,  'an' : 8338 ,  '!=' : 8153 ,  '"' : 7998 ,  'break;' : 7894 ,  '%s' : 7870 ,  'i32' : 7804 ,  'static' : 7480 ,  'RUN:' : 7463 ,  'false;' : 7426 ,  '||' : 7402 ,  'true;' : 6999 ,  '<' : 6903 ,  'unsigned' : 6832 ,  '#include' : 6637 ,  'with' : 6401 ,  'A' : 6377 ,  '{}' : 6091 ,  'or' : 5921 ,  'call' : 5876 ,  'If' : 5820 ,  '+' : 5814 ,  'function' : 5757 ,  'T>' : 5603 ,  'are' : 5538 ,  'char' : 5196 ,  'return;' : 5176 ,  'it' : 5008 ,  'as' : 4992 ,  '(const' : 4839 ,  '0,' : 4756 ,  'auto' : 4615 ,  'This' : 4606 ,  'have' : 4539 ,  'x' : 4503 ,  'virtual' : 4421 ,  'QualType' : 4402 ,  'parallel' : 4196 ,  'The' : 4084 ,  'from' : 4052 ,  '0' : 3957 ,  'nullptr;' : 3866 ,  'I' : 3840 ,  '?' : 3834 ,  '+=' : 3792 ,  'new' : 3734 ,  'T' : 3715 ,  'define' : 3615 ,  '(int' : 3597 ,  'on' : 3348 ,  'typedef' : 3336 ,  'by' : 3225 ,  'using' : 3136 ,  '++i)' : 3085 ,  'FIXME:' : 3045 ,  '\\' : 3041 ,  'B' : 3030 ,  'here}}' : 3000 ,  'no' : 2971 }

java = { '{' : 594399 ,  '}' : 582986 ,  '=' : 569661 ,  'public' : 295333 ,  '+' : 248836 ,  'if' : 199625 ,  'return' : 173455 ,  'new' : 169395 ,  'import' : 158535 ,  'int' : 133518 ,  'static' : 103148 ,  'void' : 101021 ,  'private' : 92721 ,  'long' : 91498 ,  'final' : 82146 ,  '==' : 81298 ,  'String' : 72857 ,  '!=' : 63384 ,  'throws' : 59309 ,  '"' : 57523 ,  'null)' : 53530 ,  'else' : 49292 ,  'boolean' : 45951 ,  'throw' : 40572 ,  'for' : 37175 ,  'i' : 37094 ,  '0;' : 34835 ,  'class' : 34724 ,  'null;' : 34576 ,  '<' : 33745 ,  '&&' : 32309 ,  ':' : 30912 ,  'case' : 30457 ,  'try' : 27628 ,  '0,' : 26937 ,  'catch' : 24365 ,  'false;' : 23413 ,  '0)' : 22544 ,  'extends' : 21831 ,  '-' : 21619 ,  '(int' : 20772 ,  '||' : 19489 ,  'package' : 19158 ,  'true;' : 19028 ,  'e)' : 18621 ,  'break;' : 18043 ,  ';' : 16737 ,  'null' : 16731 ,  '>' : 15823 ,  'i++)' : 15288 ,  ')' : 14413 ,  '?' : 13950 ,  '&' : 13323 ,  'Object' : 12427 ,  'String[]' : 10983 ,  '*' : 10901 ,  '+=' : 10868 ,  'while' : 10492 ,  'byte[]' : 10134 ,  'return;' : 10026 ,  'not' : 9664 ,  '1;' : 9246 ,  '>=' : 8799 ,  'null,' : 8616 ,  '0' : 8443 ,  'abstract' : 7973 ,  'true);' : 7833 ,  '1,' : 7641 ,  'Path' : 7515 ,  '};' : 7173 ,  ');' : 7094 ,  'null);' : 6739 ,  'result' : 6702 ,  'false);' : 6491 ,  'finally' : 6153 ,  '256,' : 6018 ,  '@Test' : 5959 ,  '0);' : 5710 ,  '<=' : 5605 ,  'in' : 5511 ,  'char[]' : 5369 ,  '{}' : 5325 ,  '1);' : 5325 ,  'of' : 5177 ,  'double' : 5113 ,  '|' : 5107 ,  'false,' : 5019 ,  'float' : 4959 ,  '(byte)' : 4885 ,  '19002,' : 4883 ,  'x,' : 4799 ,  'args)' : 4694 ,  '",' : 4621 ,  '20283,' : 4602 ,  '19029,' : 4508 ,  '-1;' : 4447 }


ruby = { '#' : 16500 ,  'end' : 11966 ,  '=' : 10622 ,  'the' : 6374 ,  'def' : 5902 ,  'if' : 4075 ,  'to' : 3113 ,  'a' : 2810 ,  '=>' : 1978 ,  'is' : 1975 ,  'of' : 1921 ,  'do' : 1897 ,  'and' : 1699 ,  'for' : 1604 ,  '##' : 1434 ,  'in' : 1255 ,  'unless' : 1241 ,  'be' : 1238 ,  'require' : 1174 ,  'class' : 1150 ,  '<<' : 1140 ,  'else' : 1129 ,  '==' : 1128 ,  '}' : 1084 ,  'that' : 1039 ,  'true' : 1034 ,  'this' : 957 ,  'return' : 943 ,  '{' : 935 ,  'when' : 904 ,  'then' : 904 ,  '&&' : 902 ,  'gem' : 888 ,  'not' : 823 ,  'or' : 810 ,  'nil' : 761 ,  'raise' : 747 ,  'The' : 746 ,  'are' : 735 ,  '||' : 730 ,  'with' : 704 ,  'from' : 702 ,  'name' : 668 ,  'an' : 665 ,  '"' : 643 ,  ':nodoc:' : 615 ,  'module' : 614 ,  'will' : 580 ,  '<' : 571 ,  '[]' : 544 ,  'false,' : 542 ,  'as' : 537 ,  '||=' : 523 ,  'path' : 517 ,  'nil,' : 507 ,  'by' : 495 ,  'it' : 490 ,  'on' : 488 ,  'If' : 480 ,  'false' : 471 ,  'options' : 470 ,  'version' : 463 ,  ':' : 460 ,  '?' : 456 ,  'value' : 452 ,  'rescue' : 445 ,  'given' : 439 ,  'attr_reader' : 434 ,  'file' : 433 ,  'gems' : 432 ,  '+' : 427 ,  'you' : 427 ,  'spec' : 426 ,  'frozen_string_literal:' : 412 ,  'all' : 404 ,  'Returns' : 403 ,  'can' : 391 ,  'This' : 374 ,  '1' : 367 ,  'source' : 358 ,  '@return' : 354 ,  'command' : 331 ,  '-' : 329 ,  '\\' : 320 ,  '{}' : 303 ,  'begin' : 301 ,  'result' : 296 ,  'your' : 296 ,  'dependency' : 296 ,  'set' : 295 ,  'private' : 294 ,  'use' : 282 ,  'default' : 272 ,  'Bundler' : 270 ,  'used' : 264 ,  'new' : 264 ,  'elsif' : 263 ,  '=~' : 263 ,  '*' : 261 ,  'specs' : 260 }

perl = { '=' : 71865 ,  '{' : 60869 ,  'my' : 49142 ,  '=>' : 37536 ,  '}' : 32871 ,  '#' : 25755 ,  'if' : 24830 ,  "'sub" : 23745 ,  'return' : 21174 ,  "}'," : 20523 ,  ')' : 16798 ,  '(' : 13307 ,  ');' : 11101 ,  '@_;' : 9223 ,  'the' : 8954 ,  'shift;' : 8936 ,  'unless' : 6937 ,  '};' : 6586 ,  '$self' : 6538 ,  'eq' : 6202 ,  '=~' : 6194 ,  'to' : 6146 ,  ':' : 5922 ,  'and' : 5780 ,  '?' : 5657 ,  'for' : 5653 ,  'or' : 5264 ,  'a' : 5037 ,  '||' : 4710 ,  'else' : 4381 ,  '&&' : 4378 ,  '.' : 4304 ,  'defined' : 4238 ,  'is' : 3648 ,  '$VAR1' : 3299 ,  'not' : 3252 ,  '1' : 3014 ,  'in' : 3008 ,  '0;' : 2987 ,  'push' : 2934 ,  'of' : 2921 ,  '1;' : 2786 ,  "}'" : 2537 ,  '==' : 2503 ,  'elsif' : 2460 ,  '.=' : 2425 ,  '($self,' : 2389 ,  'we' : 2319 ,  'sub' : 2298 ,  '0' : 2195 ,  'be' : 1941 ,  'return;' : 1932 ,  '-' : 1914 ,  '},' : 1893 ,  '[' : 1872 ,  'die' : 1857 ,  'foreach' : 1754 ,  'map' : 1735 ,  'croak' : 1692 ,  '$_' : 1684 ,  'print' : 1672 ,  'ref' : 1626 ,  'it' : 1620 ,  'delete' : 1617 ,  '"' : 1604 ,  'no' : 1583 ,  '||=' : 1544 ,  'local' : 1534 ,  '0,' : 1507 ,  'while' : 1476 ,  '$name' : 1437 ,  '$self,' : 1397 ,  'this' : 1396 ,  'next' : 1376 ,  'require' : 1358 ,  '>' : 1356 ,  'keys' : 1355 ,  'exists' : 1348 ,  "\\'\\';" : 1303 ,  '+' : 1296 ,  '@_' : 1265 ,  '@{' : 1253 ,  'that' : 1252 ,  'shift' : 1218 ,  '$class' : 1201 ,  '1,' : 1168 ,  'with' : 1149 ,  'eval' : 1148 ,  'as' : 1144 ,  "\\'" : 1139 ,  'an' : 1122 ,  'undef' : 1099 ,  'undef;' : 1097 ,  '$self;' : 1088 ,  'name' : 1076 ,  'from' : 1051 ,  '{};' : 1045 ,  '()' : 1039 ,  '$value' : 1011 ,  'on' : 1009 }

# perl = { '#' : 20217 ,  ';' : 13281 ,  '=' : 7507 ,  '{' : 6315 ,  '}' : 5833 ,  'LETTER' : 5626 ,  'my' : 5253 ,  'the' : 5172 ,  'CJK' : 5098 ,  'if' : 3953 ,  'LATIN' : 3229 ,  'to' : 3033 ,  'WITH' : 2987 ,  '=>' : 2438 ,  'SMALL' : 2250 ,  'is' : 2219 ,  'CAPITAL' : 2064 ,  'a' : 1945 ,  'and' : 1788 ,  'for' : 1766 ,  'of' : 1648 ,  'in' : 1543 ,  'print' : 1373 ,  '=~' : 1262 ,  'or' : 1115 ,  'sub' : 1083 ,  'MARK>' : 1035 ,  '(' : 1023 ,  ')' : 1016 ,  'use' : 974 ,  'that' : 951 ,  'KATAKANA' : 933 ,  'eq' : 883 ,  'be' : 869 ,  'unless' : 788 ,  '"' : 777 ,  'it' : 763 ,  'die' : 760 ,  'we' : 744 ,  'ACUTE' : 740 ,  'not' : 740 ,  'return' : 732 ,  'this' : 718 ,  'RADICAL' : 699 ,  'SOUND' : 696 ,  '##' : 685 ,  'U' : 684 ,  '.' : 679 ,  '-' : 668 ,  'AND' : 654 ,  '+' : 651 ,  'are' : 646 ,  'KANGXI' : 642 ,  '<LATIN' : 627 ,  'else' : 620 ,  '&&' : 606 ,  'ok' : 602 ,  ':' : 598 ,  'with' : 588 ,  'as' : 584 ,  'O' : 578 ,  ');' : 566 ,  '||' : 511 ,  '?' : 506 ,  'from' : 498 ,  'A' : 494 ,  'E' : 492 ,  'file' : 489 ,  'If' : 479 ,  'The' : 478 ,  'defined' : 470 ,  'VOICED' : 467 ,  'GRAVE' : 455 ,  'by' : 441 ,  'push' : 437 ,  'on' : 428 ,  'This' : 419 ,  'foreach' : 411 ,  'elsif' : 410 ,  'new' : 403 ,  '0;' : 403 ,  '1' : 403 ,  'will' : 402 ,  '*' : 400 ,  '1;' : 399 ,  '==' : 399 ,  'an' : 392 ,  'have' : 365 ,  '|' : 357 ,  'all' : 355 ,  'set' : 352 ,  'while' : 347 ,  '};' : 346 ,  '[' : 342 ,  'code' : 342 ,  'shift;' : 338 ,  '@_;' : 335 ,  'next' : 333 ,  '30FC' : 328 ,  'CARON' : 326 }

c = { '=' : 2676314 ,  '{' : 1368862 ,  '*' : 1254223 ,  '}' : 1051623 ,  'if' : 1022007 ,  '*/' : 854162 ,  '/*' : 807015 ,  'struct' : 703407 ,  'return' : 586933 ,  'int' : 542039 ,  'static' : 478685 ,  '0;' : 328241 ,  'for' : 229611 ,  '#include' : 227685 ,  '==' : 225465 ,  '&' : 223274 ,  '+' : 215075 ,  '0x00,' : 213429 ,  'void' : 211655 ,  'case' : 199378 ,  '#define' : 191776 ,  '},' : 187848 ,  'unsigned' : 181197 ,  'of' : 180900 ,  '-' : 178034 ,  '|' : 174062 ,  '0,' : 161034 ,  'else' : 158414 ,  '<' : 156471 ,  'break;' : 152386 ,  'goto' : 134425 ,  '};' : 129428 ,  'const' : 123385 ,  'in' : 121138 ,  '0)' : 115014 ,  'ret' : 112447 ,  '&&' : 107117 ,  '!=' : 104830 ,  'u32' : 98720 ,  '<<' : 96761 ,  'long' : 89361 ,  '|=' : 85573 ,  'char' : 84254 ,  'ret;' : 78141 ,  '||' : 76388 ,  '1;' : 73291 ,  'this' : 70846 ,  'u8' : 66476 ,  '1,' : 64523 ,  'on' : 63656 ,  '0);' : 62992 ,  'not' : 62199 ,  ':' : 61955 ,  'This' : 61835 ,  'i' : 61716 ,  'device' : 60665 ,  '>' : 60245 ,  'NULL;' : 59736 ,  '0' : 57635 ,  'or' : 56827 ,  '(i' : 55804 ,  'err' : 55224 ,  'with' : 53485 ,  '-EINVAL;' : 52526 ,  '\\' : 52301 ,  '+=' : 52252 ,  '?' : 47432 ,  '>>' : 47102 ,  'as' : 45980 ,  'return;' : 45190 ,  'NULL,' : 44293 ,  'err;' : 41835 ,  '#endif' : 41806 ,  'data' : 41289 ,  '"' : 40969 ,  '1' : 40800 ,  'i++)' : 40540 ,  'switch' : 40141 ,  '/**' : 39990 ,  'while' : 37648 ,  '>=' : 37432 ,  '&=' : 36354 ,  'i;' : 35563 ,  'flags);' : 34566 ,  '1);' : 34558 }


typescript = { '{' : 64204 ,  '}' : 49367 ,  '=' : 46513 ,  '//' : 27202 ,  'var' : 23998 ,  '////' : 14690 ,  'return' : 14608 ,  'function' : 13574 ,  'if' : 10678 ,  '=>' : 10547 ,  'export' : 8282 ,  'class' : 7461 ,  'const' : 7319 ,  'new' : 5238 ,  'of' : 5033 ,  '===' : 4939 ,  'extends' : 4572 ,  'x' : 4456 ,  '};' : 4248 ,  'case' : 4161 ,  'public' : 4046 ,  '+' : 4018 ,  'for' : 3891 ,  'string;' : 3661 ,  'type' : 3489 ,  '()' : 3469 ,  'let' : 3417 ,  'module' : 3297 ,  'number;' : 3209 ,  'in' : 3187 ,  '&&' : 3170 ,  ':' : 3070 ,  'error' : 3000 ,  '|' : 2984 ,  '*' : 2956 ,  'x:' : 2838 ,  'string' : 2586 ,  '},' : 2574 ,  'number' : 2471 ,  '||' : 2362 ,  'static' : 2344 ,  'true' : 2206 ,  'string,' : 2183 ,  '});' : 2182 ,  'x;' : 2182 ,  'else' : 2172 ,  '1;' : 2171 ,  'private' : 2171 ,  '////}' : 2171 ,  'declare' : 2105 ,  '0;' : 2086 ,  'y' : 1992 ,  '?' : 1934 ,  'y:' : 1920 ,  '<' : 1853 ,  'i' : 1801 ,  'as' : 1797 ,  'number,' : 1792 ,  '-' : 1769 ,  'import' : 1741 ,  'C' : 1732 ,  'not' : 1664 ,  'A' : 1633 ,  'with' : 1606 ,  'typeof' : 1601 ,  'this' : 1562 ,  'number)' : 1543 ,  '!==' : 1535 ,  'a:' : 1533 ,  '////var' : 1478 ,  'T;' : 1443 ,  '*/' : 1425 ,  'b' : 1419 ,  '&' : 1407 ,  'string):' : 1383 ,  'T)' : 1377 ,  'number):' : 1350 ,  '/>' : 1339 ,  'null;' : 1329 ,  '///' : 1315 ,  'this;' : 1298 ,  'any)' : 1295 ,  '/**' : 1292 ,  'ok' : 1292 ,  'kind:' : 1288 ,  'get' : 1260 ,  'void;' : 1243 ,  'text:' : 1224 ,  '1' : 1209 ,  'string)' : 1208 }


classifiers = [cplusplus, javascript, java, c, ruby, perl, typescript, python, scala, php, objc]

# Normalize classifiers

for i in range(0, len(classifiers)):
    total = reduce(lambda x,y: x+y, classifiers[i].values())
    for j in classifiers[i].keys():
        classifiers[i][j] = float(classifiers[i][j]) / total


for x in input:
    fname = x[0]
    ext = x[1]

    counts = {}
    total = 0

    # Load up input file to be classified.

    with open(fname, 'r') as f:
        # Generate histogram of counts for each word.
        wordgen = words(f)
        for word in wordgen:
            counts[word] = counts.get(word, 0) + 1
            total += 1

    argmax = 0
    max = float('-inf')
    secondMax = float('-inf')

    for i in xrange(0,len(classifiers)):

        # Naive Bayes.
        val = 1
        for word in counts:
            c       = classifiers[i].get(word, 0.0001)
            val     += math.log(counts[word] * c)

        # Incorporate a modest prior for the extension
        for thisext in extensions[i]:
            if ext == thisext:
                val /= extensionPrior
                break

        # New maximum?
        if val > max:
            secondMax = max
            max = val
            argmax = i

    print(fname + "," + classes[argmax] +  "," + str(1 - (max / secondMax)))

