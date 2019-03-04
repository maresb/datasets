import tensorflow as tf
import numpy as np
import tensorflow_datasets.public_api as tfds
import os
import tensorflow as tf
_DOWNLOAD_LINK = {"en":"https://voice-prod-bundler-ee1969a6ce8178826482b88e843c335139bd3fb4.s3.amazonaws.com/cv-corpus-1/en.tar.gz"}
_SPLITS = {tfds.Split.TRAIN:"train",tfds.Split.TEST:"test",tfds.Split.VALIDATION:"validated"}
class commonvoice(tfds.core.GeneratorBasedBuilder):
    VERSION = tfds.core.Version("1.0.0")
    def _info(self):
       return tfds.core.DatasetInfo(
       description = ("Mozilla Common Voice Dataset (English)"),
       builder = self,
       features = tfds.features.FeaturesDict({
       "client_id":tfds.features.Text(),
       "upvotes":tf.int32,
       "downvotes":tf.int32,
       "age":tfds.features.Text(),
       "gender":tfds.features.Text(),
       "accent":tfds.features.Text(),
       "sentence":tfds.features.Text(),
       "voice":tfds.features.Tensor(shape = (None,),dtype = tf.float32)
       }),
       urls = [u"https://voice.mozilla.org/en/datasets"]
       )
    def _split_generators(self,dl_manager):
        dl_path = dl_manager.extract(dl_manager.download(_DOWNLOAD_LINK))
        clip_folder = os.path.join(dl_path["en"],"clips") # Need to Check for replacement
        return [tfds.core.SplitGenerator(
        name = k,
        num_shards = 40,
        gen_kwargs = {
        "audio_path":clip_folder,
        "label_path":os.path.join(dl_path["en"],"%s.tsv"%v)
        }) for k,v in _SPLITS.items()]
    def _generate_examples(self,audio_path,label_path):
        def decode_tsv(line):
            record_defaults = [""]*8
            data = tf.decode_csv(line,record_defaults,field_delim = "\t")
            return data
        def convert(byte,type_):
            assert callable(type_)
            v = byte.decode("utf-8")
            return type_(v) if len(v)>0 else 0
        ds = tfds.as_numpy(tf.data.TextLineDataset(label_path).skip(1).map(decode_tsv))
        ffmpeg = tfds.features.Audio(file_format = "mp3")
        for id_,path,sentence,upvotes,downvotes,age,gender,accent in ds:
            wave = ffmpeg.encode_example(os.path.join(audio_path,"%s.mp3"%path.decode("utf-8"))).astype("float32")
            yield {
            "client_id":id_.decode("utf-8"),
            "voice": wave,
            "sentence":sentence.decode("utf-8"),
            "upvotes": convert(upvotes,int),
            "downvotes":convert(downvotes,int),
            "age":age.decode("utf-8"),
            "gender":gender.decode("utf-8"),
            "accent":accent.decode("utf-8")}
