#!/usr/bin/env python
# coding: utf-8
import cli

class Script():
    def __init__(self, method, pattern_ids: list, data_dir, model_type, model_name_or_path, task_name, output_dir, do_train=True, do_eval=True):
        self.method = method
        self.pattern_ids = pattern_ids
        self.data_dir = data_dir
        self.model_type = model_type
        self.model_name_or_path = model_name_or_path
        self.task_name = task_name
        self.output_dir = output_dir
        self.wrapper_type = "mlm"
        self.lm_training = False
        self.alpha=0.9999
        self.temperature=2
        self.verbalizer_file=None
        self.reduction='wmean'
        self.decoding_strategy='default'
        self.no_distillation=False
        self.pet_repetitions=3 #2 #3 #1
        self.pet_max_seq_length=256
        self.pet_per_gpu_train_batch_size=4 #2
        self.pet_per_gpu_eval_batch_size=8
        self.pet_per_gpu_unlabeled_batch_size=4
        self.pet_gradient_accumulation_steps=1 #2 #1 #4
        self.pet_num_train_epochs=2 #3 #2
        self.pet_max_steps=-1
        # Also used for final PET classifier
        self.sc_repetitions=1
        self.sc_max_seq_length=256
        self.sc_per_gpu_train_batch_size=4
        self.sc_per_gpu_eval_batch_size=8
        self.sc_per_gpu_unlabeled_batch_size=4 #2
        self.sc_gradient_accumulation_steps=1 #2 #1 #4
        self.sc_num_train_epochs=3 #2 #3 #1
        self.sc_max_steps=-1
        # iPet
        self.ipet_generations=3
        self.ipet_logits_percentage=0.25
        self.ipet_scale_factor=5
        self.ipet_n_most_likely=-1
        self.train_examples=-1
        self.test_examples=-1
        self.unlabeled_examples=-1
        self.split_examples_evenly=False
        self.cache_dir=''
        self.learning_rate=1e-05
        self.weight_decay=0.01
        self.adam_epsilon=1e-08
        self.max_grad_norm=1.0
        self.warmup_steps=0
        self.logging_steps=0 #50
        '''Set GPU support'''
        self.no_cuda=False
        self.overwrite_output_dir=True
        self.seed=42
        self.do_train=True
        self.do_eval=True
        self.priming=False
        self.eval_set='dev'
        
    def run(self):
        cli.main(self)
    
    def get(self):
    	return vars(self)
