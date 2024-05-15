# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Any, List, Optional

from langchain_text_splitters.base import Language, TextSplitter


class CharacterTextSplitter(TextSplitter):
    """Splitting text that looks at characters."""

    def __init__(
            self, separator: str = "\n\n", is_separator_regex: bool = False, **kwargs: Any
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(**kwargs)
        self._separator = separator
        self._is_separator_regex = is_separator_regex

    def split_text(self, text: str) -> List[str]:
        """Split incoming text and return chunks."""
        # First we naively split the large input into a bunch of smaller ones.
        separator = (
            self._separator if self._is_separator_regex else re.escape(self._separator)
        )
        splits = _split_text_with_regex(text, separator, self._keep_separator)
        _separator = "" if self._keep_separator else self._separator
        return self._merge_splits(splits, _separator)

def _split_text_with_regex(
        text: str, separator: str, keep_separator: bool
) -> List[str]:
    # Now that we have the separator, split the text
    if separator:
        if keep_separator:
            # The parentheses in the pattern keep the delimiters in the result.
            _splits = re.split(f"({separator})", text)
            splits = [_splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)]
            if len(_splits) % 2 == 0:
                splits += _splits[-1:]
            splits = [_splits[0]] + splits
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s != ""]


class DynamicSizeDynamicStepSplitter(TextSplitter):
    """Splitting text by recursively looking at characters and dynamically choosing separators."""

    def __init__(
            self,
            separators: Optional[List[str]] = None,
            keep_separator: bool = True,
            is_separator_regex: bool = False,
            window_size: int = 100,
            step_size: int = 50,
            length_function: Callable[[str], int] = len,
            **kwargs: Any,

    ) -> None:
        self._separators = separators or ["\n\n", "\n", ".", "。", "?", "？", "!", "！"]
        self._is_separator_regex = is_separator_regex
        self._window_size = window_size
        self._step_size = step_size
        self._keep_separator = keep_separator
        self._length_function = length_function

    def _split_text_with_regex(self, text: str, regex_separator: str) -> List[str]:
        """Helper method to split text using a regex separator."""
        if self._keep_separator:
            _splits = re.split(f"({regex_separator})", text)
            splits = [_splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)]
            if len(_splits) % 2 == 0:
                splits += _splits[-1:]
            splits = [_splits[0]] + splits
        else:
            splits = re.split(regex_separator, text)
        return [s for s in splits if s != ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks by dynamically choosing the best separator."""
        final_chunks = [text]  # Start with the entire text as the only initial chunk

        for separator in separators:
            regex_separator = separator if self._is_separator_regex else re.escape(separator)
            new_chunks = []
            for chunk in final_chunks:
                if re.search(regex_separator, chunk):
                    splits = self._split_text_with_regex(chunk, regex_separator)
                    new_chunks.extend(splits)
                else:
                    new_chunks.append(chunk)
            final_chunks = new_chunks

        # If no appropriate separator is found, use the whole text
        if not final_chunks:
            final_chunks = [text]

        # final_chunks = [(i, chunk) for i, chunk in enumerate(final_chunks)]

        # Further split the chunks based on window_size and step_size
        split_chunks = []
        for index, chunk in final_chunks:
            start_index = 0
            total_length = 0
            temp_chunk = ''
            while start_index < len(final_chunks) - index:
                total_length = total_length + len(final_chunks[index + start_index])
                temp_chunk = "".join(temp_chunk, final_chunks.index(start_index))
                if total_length >= self._window_size:
                    split_chunks.append(chunk[start_index:])
                    break
                start_index = start_index + 1

        # Remove chunks that do not exceed 100 characters in length
        split_chunks = [chunk for chunk in split_chunks if len(chunk) > 10]

        # Create list of tuples with chunk size and content
        chunk_sizes = [(len(chunk), chunk) for chunk in split_chunks]

        # Sort chunks by size in descending order
        chunk_sizes.sort(reverse=True, key=lambda x: x[0])
        print(chunk_sizes)
        return split_chunks

    def split_text(self, text: str) -> List[str]:
        """Public method to split text using configured separators."""
        return self._split_text(text, self._separators)

    @classmethod
    def from_language(
            cls, language: Language, **kwargs: Any
    ) -> DynamicSizeDynamicStepSplitter:
        separators = cls.get_separators_for_language(language)
        return cls(separators=separators, is_separator_regex=True, **kwargs)

    @staticmethod
    def get_separators_for_language(language: Language) -> List[str]:
        if language == Language.CPP:
            return [
                # Split along class definitions
                "\nclass ",
                # Split along function definitions
                "\nvoid ",
                "\nint ",
                "\nfloat ",
                "\ndouble ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\nswitch ",
                "\ncase ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.GO:
            return [
                # Split along function definitions
                "\nfunc ",
                "\nvar ",
                "\nconst ",
                "\ntype ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nswitch ",
                "\ncase ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.JAVA:
            return [
                # Split along class definitions
                "\nclass ",
                # Split along method definitions
                "\npublic ",
                "\nprotected ",
                "\nprivate ",
                "\nstatic ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\nswitch ",
                "\ncase ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.KOTLIN:
            return [
                # Split along class definitions
                "\nclass ",
                # Split along method definitions
                "\npublic ",
                "\nprotected ",
                "\nprivate ",
                "\ninternal ",
                "\ncompanion ",
                "\nfun ",
                "\nval ",
                "\nvar ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\nwhen ",
                "\ncase ",
                "\nelse ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.JS:
            return [
                # Split along function definitions
                "\nfunction ",
                "\nconst ",
                "\nlet ",
                "\nvar ",
                "\nclass ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\nswitch ",
                "\ncase ",
                "\ndefault ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.TS:
            return [
                "\nenum ",
                "\ninterface ",
                "\nnamespace ",
                "\ntype ",
                # Split along class definitions
                "\nclass ",
                # Split along function definitions
                "\nfunction ",
                "\nconst ",
                "\nlet ",
                "\nvar ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\nswitch ",
                "\ncase ",
                "\ndefault ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.PHP:
            return [
                # Split along function definitions
                "\nfunction ",
                # Split along class definitions
                "\nclass ",
                # Split along control flow statements
                "\nif ",
                "\nforeach ",
                "\nwhile ",
                "\ndo ",
                "\nswitch ",
                "\ncase ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.PROTO:
            return [
                # Split along message definitions
                "\nmessage ",
                # Split along service definitions
                "\nservice ",
                # Split along enum definitions
                "\nenum ",
                # Split along option definitions
                "\noption ",
                # Split along import statements
                "\nimport ",
                # Split along syntax declarations
                "\nsyntax ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.PYTHON:
            return [
                # First, try to split along class definitions
                "\nclass ",
                "\ndef ",
                "\n\tdef ",
                # Now split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.RST:
            return [
                # Split along section titles
                "\n=+\n",
                "\n-+\n",
                "\n\\*+\n",
                # Split along directive markers
                "\n\n.. *\n\n",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.RUBY:
            return [
                # Split along method definitions
                "\ndef ",
                "\nclass ",
                # Split along control flow statements
                "\nif ",
                "\nunless ",
                "\nwhile ",
                "\nfor ",
                "\ndo ",
                "\nbegin ",
                "\nrescue ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.RUST:
            return [
                # Split along function definitions
                "\nfn ",
                "\nconst ",
                "\nlet ",
                # Split along control flow statements
                "\nif ",
                "\nwhile ",
                "\nfor ",
                "\nloop ",
                "\nmatch ",
                "\nconst ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.SCALA:
            return [
                # Split along class definitions
                "\nclass ",
                "\nobject ",
                # Split along method definitions
                "\ndef ",
                "\nval ",
                "\nvar ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\nmatch ",
                "\ncase ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.SWIFT:
            return [
                # Split along function definitions
                "\nfunc ",
                # Split along class definitions
                "\nclass ",
                "\nstruct ",
                "\nenum ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\ndo ",
                "\nswitch ",
                "\ncase ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.MARKDOWN:
            return [
                # First, try to split along Markdown headings (starting with level 2)
                "\n#{1,6} ",
                # Note the alternative syntax for headings (below) is not handled here
                # Heading level 2
                # ---------------
                # End of code block
                "```\n",
                # Horizontal lines
                "\n\\*\\*\\*+\n",
                "\n---+\n",
                "\n___+\n",
                # Note that this splitter doesn't handle horizontal lines defined
                # by *three or more* of ***, ---, or ___, but this is not handled
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.LATEX:
            return [
                # First, try to split along Latex sections
                "\n\\\\chapter{",
                "\n\\\\section{",
                "\n\\\\subsection{",
                "\n\\\\subsubsection{",
                # Now split by environments
                "\n\\\\begin{enumerate}",
                "\n\\\\begin{itemize}",
                "\n\\\\begin{description}",
                "\n\\\\begin{list}",
                "\n\\\\begin{quote}",
                "\n\\\\begin{quotation}",
                "\n\\\\begin{verse}",
                "\n\\\\begin{verbatim}",
                # Now split by math environments
                "\n\\\begin{align}",
                "$$",
                "$",
                # Now split by the normal type of lines
                " ",
                "",
            ]
        elif language == Language.HTML:
            return [
                # First, try to split along HTML tags
                "<body",
                "<div",
                "<p",
                "<br",
                "<li",
                "<h1",
                "<h2",
                "<h3",
                "<h4",
                "<h5",
                "<h6",
                "<span",
                "<table",
                "<tr",
                "<td",
                "<th",
                "<ul",
                "<ol",
                "<header",
                "<footer",
                "<nav",
                # Head
                "<head",
                "<style",
                "<script",
                "<meta",
                "<title",
                "",
            ]
        elif language == Language.CSHARP:
            return [
                "\ninterface ",
                "\nenum ",
                "\nimplements ",
                "\ndelegate ",
                "\nevent ",
                # Split along class definitions
                "\nclass ",
                "\nabstract ",
                # Split along method definitions
                "\npublic ",
                "\nprotected ",
                "\nprivate ",
                "\nstatic ",
                "\nreturn ",
                # Split along control flow statements
                "\nif ",
                "\ncontinue ",
                "\nfor ",
                "\nforeach ",
                "\nwhile ",
                "\nswitch ",
                "\nbreak ",
                "\ncase ",
                "\nelse ",
                # Split by exceptions
                "\ntry ",
                "\nthrow ",
                "\nfinally ",
                "\ncatch ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.SOL:
            return [
                # Split along compiler information definitions
                "\npragma ",
                "\nusing ",
                # Split along contract definitions
                "\ncontract ",
                "\ninterface ",
                "\nlibrary ",
                # Split along method definitions
                "\nconstructor ",
                "\ntype ",
                "\nfunction ",
                "\nevent ",
                "\nmodifier ",
                "\nerror ",
                "\nstruct ",
                "\nenum ",
                # Split along control flow statements
                "\nif ",
                "\nfor ",
                "\nwhile ",
                "\ndo while ",
                "\nassembly ",
                # Split by the normal type of lines
                "\n\n",
                "\n",
                " ",
                "",
            ]
        elif language == Language.COBOL:
            return [
                # Split along divisions
                "\nIDENTIFICATION DIVISION.",
                "\nENVIRONMENT DIVISION.",
                "\nDATA DIVISION.",
                "\nPROCEDURE DIVISION.",
                # Split along sections within DATA DIVISION
                "\nWORKING-STORAGE SECTION.",
                "\nLINKAGE SECTION.",
                "\nFILE SECTION.",
                # Split along sections within PROCEDURE DIVISION
                "\nINPUT-OUTPUT SECTION.",
                # Split along paragraphs and common statements
                "\nOPEN ",
                "\nCLOSE ",
                "\nREAD ",
                "\nWRITE ",
                "\nIF ",
                "\nELSE ",
                "\nMOVE ",
                "\nPERFORM ",
                "\nUNTIL ",
                "\nVARYING ",
                "\nACCEPT ",
                "\nDISPLAY ",
                "\nSTOP RUN.",
                # Split by the normal type of lines
                "\n",
                " ",
                "",
            ]

        else:
            raise ValueError(
                f"Language {language} is not supported! "
                f"Please choose from {list(Language)}"
            )

if __name__ == '__main__':
    text = '郗鉴（东晋重臣、书法家）\n郗鉴（269年－339年），字道徽。高平郡金乡县（今山东省金乡县）人。东晋重臣、书法家，东汉御史大夫郗虑玄孙。郗鉴少年时孤贫，但博览经籍、躬耕吟咏，以清节儒雅著名，不应朝廷辟名。晋惠帝时曾为太子中舍人、中书侍郎。永嘉之乱时，聚众避难于峄山。其后被琅邪王司马睿授为兖州刺史。永昌初年，入朝任领军将军、安西将军、尚书令等职。参与讨平王敦之乱、苏峻之乱，并与王导、卞壸等同受遗诏辅晋成帝。累官司空、侍中，封南昌县公。咸康四年（338年），拜太尉。他拒绝外戚庾亮废王导的建议，阻止了朝中的士族斗争。咸康五年（339年），郗鉴去世，年七十一。获赠太宰，谥号“文成”。郗鉴工于书法，现有《灾祸帖》存于《淳化阁帖》中，原有文集十卷，今已遗失，《全晋文》录其作品。\nTA说 从流民首领到制衡门阀士族的东晋能臣，此人却常被史家低估2018-09-26 21:51 提起东晋，史家向来重论王谢桓庾四大盛门及其领头人物。但有这么一个人，并非出身顶级门阀，以“流民帅”身份南下，却两拜三公之位，制衡门阀士族，拱卫京师，为明帝托孤重臣，对东晋偏安江左贡献极大。他就是郗鉴，一个常被世人低估的东晋能臣。...详情 相关新闻 内容来自 郗鉴人物生平 郗鉴初入仕途 郗鉴是东汉末年的御史大夫郗虑的玄孙，从小孤贫，但仍然博览经籍，即使耕作时仍不断吟咏文章，以儒雅著名。及后任赵王司马伦的掾属，但察觉到赵王有夺权篡位之心后，他便称病辞官。 永康二年（301年），司马伦篡位称帝，其党羽都擢升要职，但郗鉴则闭门自守，不与他们接触。同年，司马伦被推翻，惠帝复位，郗鉴参司空（刘寔）军事，后历任太子中舍人、中书侍郎。 后来被东海王司马越辟为主簿，举贤良，但郗鉴都不接受。征东大将军苟晞征辟郗鉴为从事中郎，因苟晞和司马越不和，郗鉴亦不应召，苟晞也未强迫他。 [1] 郗鉴避乱峄山 永嘉五年（311年），汉赵军队攻陷洛阳，并俘掳晋怀帝，北方陷入空前的混乱，郗鉴亦被乞活军首领陈午部众所获。同乡人张萛先前要和郗鉴相交，郗鉴不予理睬，这时，张萛到陈午的军营来探视看望郗鉴，既而召郗鉴为卿。郗鉴对张萛说：“我们同处一乡，但情义不曾相通，你怎么能乘着混乱这样胡为呢！”张萛非常惭愧，知趣地退走了。陈午因为郗鉴素有有名望，打算推郗鉴为首领，只因郗鉴及时逃脱而未能成事。 直到陈午兵败溃散，郗鉴才回归故乡。当时正值大饥荒之年，州中人士平素感于郗鉴恩义的，都来接济资助于他。郗鉴将所得到的馈赠，分别送给亲族和乡里孤贫老弱，靠他的接济得以幸存的人很多，大家相互商议说：“如今天子流亡在外，中原无主，我们应依靠仁德之人，才能够渡过难关，免得死于乱中。”大家就推举郗鉴为主，一千多户一起跟随郗鉴，到鲁地的峄山中避难。 [2] 晋元帝司马睿镇守江左时，以郗鉴为龙骧将军、兖州刺史，出镇邹山。当时郗鉴与荀藩所派的李述和刘琨所派的刘演同居兖州刺史，三人由不同行台承制任命，各据一郡，并各自为政，互相对立。同时兖州亦正受徐龛和石勒两股军事力量侵扰。在战事不息而没有外援之下闹饥荒，虽然人民要捕野鼠燕子等动物来充饥，但仍不叛离郗鉴，反而人数渐多，三年之间就拥众数万。司马睿因而加授其为辅国将军、都督兖州诸军事。 [3] 当时兖州以郗鉴为方伯，阮放为宏伯，胡毋辅之为达伯，卞壶为裁伯，蔡谟为朗伯，阮孚为诞伯，刘绥为委伯，羊曼为濌伯，八人并称“兖州八伯”。 [4] 郗鉴入朝任职 永昌元年（322年），郗鉴因后赵逼近的压力退守合肥。同年，被征为领军将军，到建康后改授尚书，郗鉴因病而不接任。不久，发生王敦之乱，元帝被软禁，因而忧愤而死。元帝驾崩后，由太子司马绍继位，即明帝。明帝即位后因畏惧大权在握的王敦，内外交困，便想以郗鉴为外援。 太宁元年（323年），明帝任命郗鉴为兖州刺史、都督扬州江西诸军、假节，镇合肥。王敦对此十分忌惮，于是表郗鉴为尚书令，征召他回朝。 [5] 郗鉴助平王敦 郗鉴回建康时经过王敦驻屯的姑孰 ，并与王敦相见。王敦对他说：“乐广其人无才，一个后生四处流荡，言行有背于名教朝纲，看看他的实际才能，怎么比得上满奋呢。”郗鉴回答说：“相比一定要同类型的人才行。乐广为人性情平淡，见识深远，处于倾危之朝，不随意亲附疏远于人。在愍怀太子被废时，可以说柔中有刚，不失正体。满奋是失节之人，怎能和乐广相提并论。”王敦又说：“愍怀太子被废之际，和他来往就会给自己带来危机，人怎么能死守着常理呢？以此相比，满奋不弱于乐广是很清楚的。”郗鉴说：“大丈夫洁身北面侍君，谨守三纲之义，怎么可以偷生而变节，这样有何面目居于天地之间！如果是天道已终，也当随之存亡。” 王敦早就有了无君野心，听到郗鉴这番话，心中大为不满，便不再与之相见，将郗鉴扣留下来不让他离开。王敦党徒常常诬陷郗鉴，但郗鉴仍然神态自若，一点儿也不害怕。王敦对钱凤说：“郗道徽是儒雅之士，有名望地位，怎么能随便加害于他呢！”将他释放。郗鉴回朝后便与明帝商议平灭王敦之事。 [6] 太宁二年（324年），钱凤等人领兵进逼建康，明帝以郗鉴为假节行卫将军、都督从驾诸军事。当时王敦军尚未完成集结，有人认为应率先由明帝亲自领兵进攻。但郗鉴认为敌军兵多不能力敌，而且王敦军来是已经惹来百姓极大的怨恨和反抗意识，亦无大方略，只求一战取胜。故此认为应当拖长战事，让其他反抗力量形成并对王敦进攻，藉以取胜。明帝听从了他的意见。郗鉴以尚书令的身份统领各屯营御敌，不久又派兵奇袭并大败王含军，四方义兵亦冒起，最终成功讨平王敦之乱。 [7] 郗鉴辅政重臣 王敦之乱被平定后，温峤上表提议，请求宽恕王敦的佐吏部属，郗鉴认为，先王推崇君臣礼教，崇尚为气节而捐躯，若是昏庸腐败的君主，才可开放城门以迎义师。王敦的僚属虽说多为王敦所逼，但居于叛逆的伪朝之中，没有出关投诚的义举，按照前代的古训，应该加以责罚。温峤又奏请因钱凤之母年高八十，应该免于治罪，朝廷同意所奏。 郗鉴因功获封高平侯，赐绢四千八百匹。明帝因郗鉴有才识名望，朝廷大小事情都询问他，并诏令郗鉴为朝廷起草表疏诏告，任其简易从事。王导提议追赠周札官职，郗鉴认为不合赏罚之理，王导不听，郗鉴于是驳斥他说：“王敦叛乱，相持很久不能入城，因为周札为他打开城门，才使王师遭到失败。如果王敦先前的举动，如同齐桓公、晋文公一样是正义的，那么先帝不就成了周幽王、厉王那样的昏暴之君吗？”朝臣们对此虽没有反对的，但也没人支持。 太宁三年（325年），迁任车骑将军、都督徐兖青三州军事、兖州刺史、假节，出镇广陵。 同年，明帝驾崩，郗鉴与王导、卞壶、温峤、庾亮、陆晔等一起接受遗诏，辅佐年幼的成帝司马衍。郗鉴因而晋位车骑大将军、开府仪同三司，加散骑常侍。 [8] 郗鉴义兵勤王 咸和元年（326年），郗鉴加领徐州刺史。 咸和二年（327年），苏峻和祖约发动叛变，进攻建康。郗鉴知道后打算亲自领兵营救，但朝廷却以防御北方进攻而阻止，郗鉴唯有派司马刘矩领三千人保卫建康，但次年建康便沦陷，刘矩亦退还。 中书令庾亮在建康失陷时出走，到寻阳投靠温峤，并宣庾太后口诏，升郗鉴为司空。郗鉴所在的广陵临近后赵边境，城孤粮绝，军民因对北方南侵的畏惧而没有坚守的决心。 郗鉴接受了诏命后，感激涕零，设立坛场，宰杀白马，与三军一起对天盟誓，誓言说：“贼臣祖约、苏峻不恭顺天命，不怕王师诛讨，凶暴逆行，破坏国家纲纪，无视五常之伦理，动摇国家根基，威逼胁迫幼小的君王，毁坏国家的栋梁支柱，残害忠良之臣，祸及黎民百姓，使天地神祗祖宗灵位无所归依。所以天下为之怨恨，亿万人民为之泣血，我们奉旨讨伐，以除灭元凶。过去戎狄危及周室，齐桓公与诸侯会盟以扶王室，董卓欺凌汉宫，各路豪杰聚义致讨，护卫君亲之义，古今一样。现今主上陷于危难，百姓处于倒悬，忠臣志士无不心存报国之念。凡入我同盟者，一经盟誓之后，齐心合力，以救社稷。若二寇不消灭，决不退缩偷安。有谁违背誓言，天神不容！”郗鉴登坛后慷慨陈辞，使三军士气大振。 郗鉴见此，于是派将军夏侯长通知温峤，并预计苏峻会挟持成帝到会稽，建议温峤在重要据点立营据守以阻其去路，同时又断绝粮运和坚壁清野，据守京口等待苏峻因缺乏物资溃败。温峤深表同意。 [9] 咸和三年（328年），陶侃获推举为盟主，郗鉴加都督扬州八郡军事。郗鉴后率众渡江，在茄子浦与陶侃会合，又修筑白石垒。不久王舒和虞潭战败，郗鉴与后将军郭默回屯京口，修筑大业、曲阿和庱亭三垒抵抗并分散对方军力，但随即就被围攻，郭默更逃出驻守的大业垒，令士兵震惊；但郗鉴仍坚持固守。不久苏峻堕马被杀，大业垒得以解围。 咸和四年（329年），郗鉴派参军李闳追击南逃吴兴的苏逸等人，将苏逸斩杀并收降其余众共一万多人。 [10] 郗鉴经营京口 苏峻之乱平定后，郗鉴以功升任司空，加侍中，解任八郡都督，改封为南昌县公，并以先前的爵位封其子郗昙。 咸和六年（331年），石勒部将刘征再次侵扰东南诸郡。郗鉴驻屯京口，并加都督扬州之晋陵郡、吴郡诸军事，率兵将刘征击退。 [11] 郗鉴协调士族 丞相王导在成帝继位后一直参与辅政工作，而他行事作风不拘小节，对自己委任将领的犯法行为多作容忍，招到朝臣不满，其他士族亦试图借此废掉王导，削弱琅琊王氏的影响力。陶侃就曾于成帝咸和年间打算起兵废掉王导，但因郗鉴反对而没有成事。 咸康四年（338年），郗鉴升任太尉。当时，征西将军庾亮也想罢黜王导，并寻求郗鉴的支持，但郗鉴表示反对；庾亮再写信游说郗鉴，但郗鉴坚拒，最终庾亮亦唯有放弃。郗鉴阻止了朝中主要士族的剧烈斗争，让经历了两次大动乱的东晋能够维持安定。 咸康五年（339年），郗鉴病重，将府中事务交给长史刘遐，上疏请求辞职，并推荐蔡谟为都督、徐州刺史，来接替自己。还推荐自己的侄子郗迈为兖州刺史。此疏上奏后，朝廷便任命蔡谟为太尉（郗鉴）军司。 [12-13] 同年，郗鉴病逝，享年七十一岁。成帝派御史持节护丧事，以太牢礼祭祀，追赠太宰，谥号文成。 [14] 郗鉴主要成就 永嘉之乱时，郗鉴避难于峄山、邹山，招抚流民，抵抗石勒等部，聚众至数万。 [2] [3] 晋明帝即位后，郗鉴回到建康，与明帝商议平灭图谋不轨的大将军王敦。 [6] 太宁二年（324年），统领各屯营对抗进攻建康的叛军大将钱凤等部，又派兵奇袭并大败叛党王含，成功讨平王敦之乱。 [7] 咸和二年（327年），苏峻之乱爆发，郗鉴坚守广陵。 [9] 之后更渡江，与勤王义军会合，旋即回屯京口，修筑大业、曲阿和庱亭三垒，以抵御叛军进攻。咸和四年（329年），派部下追斩逃窜的叛军首领苏逸等，收降残部一万余人。 [10] 郗鉴与重臣王导、卞壸等同受遗诏辅晋成帝，统领南下流民，长年屯驻于京口（北府），以防御后赵侵扰，并护卫建康朝廷。 [8] [11] 他拒绝大将陶侃、外戚庾亮废王导的建议，“协调当权诸门阀士族之间的关系” [15] ，阻止了朝中的士族斗争。 [16] 郗鉴个人作品 郗鉴工于书法，有《灾祸帖》存于《淳化阁帖》中。 郗鉴有文集十卷传世，今已佚。《全晋文》录有《上疏逊位》、《周札加赠议》、《又驳》、《书》。 [17] 郗鉴人物评价 纪瞻：伏见前辅国将军郗鉴，少立高操，体清望峻，文武之略，时之良干。昔与戴若思（戴渊）同辟，推放荒地，所在孤特，众无一旅，救援不至。然能绥集残余，据险历载，遂使凶寇不敢南侵。但士众单寡，无以立功，既统名州，又为常伯。若使鉴从容台闼，出内王命，必能尽抗直之规，补衮职之阙……以鉴年时，则与若思同；以资，则俱八坐。况鉴雅望清重，一代名器。 [18-19] （《请徵郗鉴疏》） 王敦：郗道徽儒雅之士，名位既重，何得害之！ [16] （《晋书》引） 陶侃：司空鉴简素贞正，内外惟允。 [20-21] （《上表逊位》） 司马衍：惟公道德冲邃，体识弘远，忠亮雅正，行为世表，历位内外，勋庸弥著。乃者约峻狂狡，毒流朝廷，社稷之危，赖公以宁。功侔古烈，勋迈桓文。 [16] [22] （《赠郗鉴爵谥册》） 孙绰：摛藻风云，策名帝录。肇阶方尺，遂隆台岳。王室未休，吾何以豫？兴言再慨，思康天步。将俾皇化，归之大素。彼苍者天，曾不遐祚。哲人其萎，民斯攸慕。嗟尔后昆，式瞻宏度。 [23] （《太宰郗鉴碑》） 房玄龄：①道徽儒雅，柔而有正，协德始安，颇均连璧。 [16] （《晋书》）②道徽忠劲，高芬远映。 [16] （《晋书》） 洪迈：百年之间，会稽王昱（司马昱）、道子（司马道子）、元显（司马元显）以宗室，王敦、二桓（桓温、桓玄）以逆取，姑置勿言，卞壶、陆玩、郗鉴、陆晔、王彪之、坦之（王坦之）不任事，其真托国者，王导、庾亮、何充、庾冰、蔡谟、殷浩、谢安、刘裕八人而已。 [24] （《容斋随笔》） 胡三省：庾亮之谋，微郗鉴拒之于外，孙盛谏止于内，必再乱天下矣。 [25] （《资治通鉴》注） 王夫之：①其时，纪瞻、卞壶、陶侃、郗鉴之俦，林立于江左，而以上流兵柄授之于王敦，导岂有不逞之谋哉？ [26] （《读通鉴论》）②郗公爱子死而不哭，卞令力疾战而丧元，二君子者，无诸己非诸人，危言以定褒贬，非导之所能也。 [27] （《读通鉴论》）③东晋之臣，可胜大臣之任者，其为郗公乎！ [27] （《读通鉴论》）④峻虽反，主虽危，而终平大难者，郗鉴、温峤也，以死殉国者，卞壶也，皆亮所引与同卫社稷者也。 [27] （《读通鉴论》） 蔡东藩：君明还要仗臣忠，一德同心始立功。莫道茂弘堪寄命，赤心到底让郗公。 [28] （《两晋演义》） 田余庆：苏峻乱平后，江左相对安定，无内战七十年，遂得以拒胡族于淮汉，息斯民于江左，郗鉴所起的积极作用，是巨大的……大臣之任，不重在操持庶政，而重在执道经邦，东晋皇权不振，大臣更应如此。郗鉴南来后，最重要的邦国大计，莫过于协调当权诸门阀士族之间的关系，杜绝觊觎，以稳定一个抗胡政权，使人民得以生存。郗鉴在这方面的作为，与其它门阀士族之居位者相比较，可称述者较多，可指责者较少。 [15] （《东晋门阀政治》） 郗鉴轶事典故 郗鉴体有三反 名臣卞壸曾经指出郗鉴身上的三种矛盾现象： 侍奉君主很正直，却喜欢下属奉承自己（方于事上，好下佞己）； 很注意加强清廉节操方面的修养，却非常喜欢计较财物得失（治身清贞，大修计校）； 自己喜欢读书，却讨厌别人做学问（自好读书，憎人学问）。 [29] 郗鉴相互推崇 晋明帝曾问名士周顗 ：“你自己认为你和郗鉴相比，谁更强些？”周顗说：“郗鉴和臣相比，似乎更有功力。”明帝又问郗鉴，郗鉴说：“周顗和臣相比，有国士家风。” [30] '
    ## window_size是窗口大小 512 1024 2048， step_size是步长 1, 2, 4
    text_splitter = DynamicSizeDynamicStepSplitter(window_size=500, step_size=1)
    all_splits = text_splitter.split_text(text)
    # print(all_splits)
