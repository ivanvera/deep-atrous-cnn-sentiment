import collections
import pandas as pd
import re
from abc import abstractclassmethod


class BasePreprocessor(object):
    _CLEAN_PREFIX = 'clean_'
    _METADATA_PREFIX = 'metadata_'
    _PAD_TOKEN = '<PAD>'
    _UNK_TOKEN = '<UNK>'
    _EOS_TOKEN = '<EOS>'

    _VOCABULARY_SIZE = 20000

    def __init__(self, path, filename, separator, vocabulary_size=_VOCABULARY_SIZE, pad_token=_PAD_TOKEN,
                 unk_token=_UNK_TOKEN, eos_token=_EOS_TOKEN):
        self._regex = re.compile('[%s]' % re.escape(r"""#"$%&'()*+/:;<=>@[\]^_`{|}~"""))
        self._remove_space_after_quote = re.compile(r'\b\'\s+\b')
        self._add_space = re.compile('([.,!?()-])')
        self._remove_spaces = re.compile('\s{2,}')
        self.path = path
        self.filename = filename
        self.separator = separator
        self.pad_token = pad_token
        self.unk_token = unk_token
        self.eos_token = eos_token
        self.vocabulary_size = vocabulary_size
        self._dictionary = {}

        self.data = self._read_file(path, filename, separator)
        self.new_data = None

    def _build_dictionary(self, data):
        all_text = []

        for review in data.review:
            all_text.extend(review.split())

        all_words = [(self.pad_token, -1), (self.unk_token, -1), (self.eos_token, -1)]
        all_words.extend(collections.Counter(all_text).most_common(self.vocabulary_size - 3))

        for word in all_words:
            if word[0] not in self._dictionary:
                self._dictionary[word[0]] = len(self._dictionary)

        metadata = pd.DataFrame(data=all_words, columns=['Word', 'Frequency'])
        self.vocabulary_size = len(self._dictionary)

        print('Built vocabulary with size: %d' % self.vocabulary_size)
        metadata.to_csv(self.path + self._METADATA_PREFIX + self.filename, sep=self.separator, index=False)
        print('Saved vocabulary to metadata file')

    def save_preprocessed_file(self):
        assert self.new_data is not None, 'No preprocessing has been applied, did you call apply_preprocessing?'

        self.new_data.to_csv(self.path + self._CLEAN_PREFIX + self.filename, sep=self.separator, index=False)
        print('Successfully saved preprocessed file')

    def apply_preprocessing(self, column_name):
        assert self.data is not None, 'No input data has been loaded'

        new_data = self.data.copy()
        new_data[column_name] = new_data[column_name].apply(lambda x: self._preprocess(x))
        self._build_dictionary(new_data)

        self.new_data = new_data
        print('Applied preprocessing to input data')

    def _preprocess(self, entry):
        entry = self._regex_preprocess(entry)
        entry = self._custom_preprocessing(entry)

        return entry

    @abstractclassmethod
    def _custom_preprocessing(self, entry):
        """
        Apply custom preprocessing to single data entry. 
        :param entry: 
        :return: the entry after custom preprocessing
        """

        return entry

    def _regex_preprocess(self, entry):
        entry = self._add_space.sub(r' \1 ', entry)
        entry = self._regex.sub('', entry)
        entry = self._remove_space_after_quote.sub(r"'", entry)
        entry = self._remove_spaces.sub(' ', entry).lower().strip()

        return entry

    def _read_file(self, path, filename, separator):
        data = pd.read_csv(path + filename, sep=separator)

        return data