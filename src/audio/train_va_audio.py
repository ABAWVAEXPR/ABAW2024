import sys

sys.path.append('src')

import os
import pprint
import datetime
from copy import deepcopy

import numpy as np

import torch
from torchvision import transforms

from audio.config import config_va

from audio.augmentation.wave_augmentation import RandomChoice, PolarityInversion, WhiteNoise, Gain

from audio.data.abaw_vae_dataset import AbawVAEDataset, VAEGrouping

from audio.net_trainer.net_trainer import NetTrainer, ProblemType

from audio.loss.loss import VALoss

from audio.models.audio_va_models import VAModelV1, VAModelV2, VAModelV3

from audio.utils.data_utils import get_source_code

from audio.utils.accuracy_utils import va_score, v_score, a_score
from audio.utils.common_utils import define_seed
        

def main(config: dict) -> None:
    """Trains with configuration in the following steps:
    - Defines datasets names
    - Defines data augmentations
    - Defines ExprDatasets
    - Defines NetTrainer
    - Defines Dataloaders
    - Defines model
    - Defines weighted loss, optimizer, scheduler
    - Runs NetTrainer 

    Args:
        config (dict): Configuration dictionary
    """
    audio_root = config['FILTERED_WAV_ROOT'] if config['FILTERED'] else config['WAV_ROOT']
    video_root = config['VIDEO_ROOT']
    labels_root = config['LABELS_ROOT']
    features_root = config['FEATURES_ROOT']
    
    logs_root = config['LOGS_ROOT']
    model_cls = config['MODEL_PARAMS']['model_cls']
    model_name = config['MODEL_PARAMS']['args']['model_name']
    aug = config['AUGMENTATION']
    num_epochs = config['NUM_EPOCHS']
    batch_size = config['BATCH_SIZE']
    
    source_code = 'Configuration:\n{0}\n\nSource code:\n{1}'.format(
        pprint.pformat(config), 
        get_source_code([main, model_cls, AbawVAEDataset, NetTrainer]))    

    ds_names = {
        'train': 'train', 
        'devel': 'validation'
    }
    
    metadata_info = {}
    all_transforms = {}
    for ds in ds_names:
        metadata_info[ds] = {
            'label_filenames': os.listdir(os.path.join(labels_root, '{0}_Set'.format(ds_names[ds].capitalize()))),
            'dataset': '{0}_Set'.format(ds_names[ds].capitalize()),
        }
        
        if 'train' in ds:
            if aug:
                all_transforms[ds] = [
                    transforms.Compose([
                        RandomChoice([PolarityInversion(), WhiteNoise(), Gain()]),
                    ]),
                ]
            else:
                all_transforms[ds] = [
                    None
                ]
        else:
            all_transforms[ds] = None


    datasets = {}
    for ds in ds_names:
        if 'train' in ds:
            datasets[ds] = torch.utils.data.ConcatDataset([
                AbawVAEDataset(
                    audio_root=audio_root,
                    video_root=video_root,
                    labels_va_root=labels_root,
                    labels_expr_root=None,
                    label_filenames=metadata_info[ds]['label_filenames'],
                    dataset=metadata_info[ds]['dataset'],
                    features_root=features_root,
                    va_frames_grouping=VAEGrouping.F2F,
                    expr_frames_grouping=None,
                    multitask=False,
                    shift=2, min_w_len=2, max_w_len=4, processor_name=model_name,
                    transform=t) for t in all_transforms[ds]
                ]
            )
        else:
            datasets[ds] = AbawVAEDataset(
                    audio_root=audio_root,
                    video_root=video_root,
                    labels_va_root=labels_root,
                    labels_expr_root=None,
                    label_filenames=metadata_info[ds]['label_filenames'],
                    dataset=metadata_info[ds]['dataset'],
                    features_root=features_root,
                    va_frames_grouping=VAEGrouping.F2F,
                    expr_frames_grouping=None,
                    multitask=False,
                    shift=2, min_w_len=2, max_w_len=4, processor_name=model_name,
                    transform=all_transforms[ds],
                )

    
    define_seed(0)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
    experiment_name = '{0}{1}-{2}'.format('a-' if aug else '-',
                                          model_cls.__name__.replace('-', '_').replace('/', '_'),
                                          datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
        
    net_trainer = NetTrainer(log_root=logs_root,
                             experiment_name=experiment_name,
                             problem_type=ProblemType.REGRESSION,
                             metrics=[va_score, v_score, a_score],
                             device=device,
                             c_names=None,
                             group_predicts_fn=None,
                             source_code=source_code)
        
    dataloaders = {}
    for ds in ds_names:
        dataloaders[ds] = torch.utils.data.DataLoader(
            datasets[ds],
            batch_size=batch_size,
            shuffle=('train' in ds),
            num_workers=batch_size if batch_size < 9 else 8)
    

    model = model_cls.from_pretrained(model_name)
    
    model.to(device)
    
    loss = VALoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer,
                                                                     T_0=10, T_mult=1,
                                                                     eta_min=0.001 * 0.1)

    model, max_perf = net_trainer.run(model=model, loss=loss, optimizer=optimizer, scheduler=scheduler,
                                      num_epochs=num_epochs, dataloaders=dataloaders, mixup_alpha=None)

    for phase in ds_names:
        if 'train' in phase:
            continue

        print()
        print(phase.capitalize())
        print('Epoch: {}, Max performance:'.format(max_perf[phase]['epoch']))
        print([metric for metric in max_perf[phase]['performance']])
        print([max_perf[phase]['performance'][metric] for metric in max_perf[phase]['performance']])
        print()


def run_va_training() -> None:
    """Wrapper for training va challenge
    """
    
    model_cls = [VAModelV1, VAModelV2, VAModelV3]
    
    for augmentation in [True, False]:
        for filtered in [True, False]:
            for m_cls in model_cls:
                cfg = deepcopy(config_va)
                cfg['FILTERED'] = filtered
                cfg['AUGMENTATION'] = augmentation
                cfg['MODEL_PARAMS']['model_cls'] = m_cls
                
                main(cfg)


if __name__ == '__main__':
    # main(config=config_vae)
    run_va_training()