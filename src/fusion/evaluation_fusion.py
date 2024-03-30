from typing import Tuple, List

import numpy as np
import pandas as pd
import torch
from scipy.special import softmax

from evaluation_dynamic import __average_predictions_on_timesteps, __interpolate_to_100_fps, \
    __synchronize_predictions_with_ground_truth, __apply_hamming_smoothing
from video.preprocessing.labels_preprocessing import load_AffWild2_labels


def load_labels(path_to_labels: str, challenge:str, video_to_fps:dict)->pd.DataFrame:
    non_filtered_labels = load_AffWild2_labels(path_to_labels, challenge)
    labels = {video_name: non_filtered_labels[video_name] for video_name in video_to_fps.keys()} # nice crutch, but we need it for now

    # calculate timesteps and num_frames
    for video_name, video_info in labels.items():        
        video_fps = video_to_fps[video_name]
        fps_in_seconds = 1. / video_fps
        num_frames = np.arange(1, video_info['category' if challenge == 'Exp' else 'valence'].shape[0]+1, 1).astype('int32')
        timesteps = num_frames * fps_in_seconds
        timesteps = np.round(timesteps, 2)
        video_info['timesteps'] = timesteps
        video_info['num_frames'] = num_frames
    return labels


def generate_test_labels(total_num_frames:dict, challenge:str, video_to_fps:dict)->pd.DataFrame:
    labels = {}
    for video_name, video_fps in video_to_fps.items():
        video_info = {}
        fps_in_seconds = 1. / video_fps
        num_frames = np.arange(1, total_num_frames[video_name] + 1, 1).astype('int32')
        categories = np.zeros((len(num_frames), 1 if challenge == 'Exp' else 2)).astype('int32')
        timesteps = num_frames * fps_in_seconds
        timesteps = np.round(timesteps, 2)

        if challenge == 'Exp':
            video_info['category'] = np.zeros((len(num_frames))).astype('int32')
        else:
            video_info['valence'] = np.zeros((len(num_frames))).astype('int32')
            video_info['arousal'] = np.zeros((len(num_frames))).astype('int32')

        video_info['timesteps'] = timesteps
        video_info['num_frames'] = num_frames
        labels[video_name] = pd.DataFrame.from_dict(video_info)
    
    return labels


def evaluate_model_full_fps(targets, predicts:List[np.ndarray], sample_info:List[dict])->Tuple[np.ndarray, np.ndarray]:
    targets = None
    # get unique values of filenames in sample_info
    video_to_fps = {sample['video_name']: float(sample['fps']) for sample in sample_info}
    total_num_frames = {sample['video_name']: sample['total_num_frames'] for sample in sample_info}
    challenge = sample_info[0]['challenge']
    # load dev labels
    if 'Test' in sample_info[0]['path_to_labels']:
        dev_labels = generate_test_labels(total_num_frames=total_num_frames, challenge=challenge, video_to_fps=video_to_fps)
    else:
        dev_labels = load_labels(sample_info[0]['path_to_labels'], challenge=challenge, video_to_fps=video_to_fps)
    
    # divide predictions on video level
    video_predictions = {sample['video_name']: [] for sample in sample_info}
    for prediction, sample in zip(predicts, sample_info):
        timestep_start = float(sample['timestep_start'])
        timestep_end = float(sample['timestep_end'])
        frame_start = int(sample['frame_start'])
        frame_end = int(sample['frame_end'])
        num_predictions = prediction.shape[0]
        # generate timesteps for predictions
        timesteps = np.linspace(timestep_start, timestep_end, num_predictions)
        num_frames = np.linspace(frame_start, frame_end, num_predictions)
        timesteps = np.round(timesteps, 2)
        num_frames = np.round(num_frames, 0)
        video_predictions[sample['video_name']].append((num_frames, timesteps, prediction))
    # now we have predictions per video
    # go over every video
    all_predictions = []
    all_timesteps = []
    all_labels=[]
    all_labels_timesteps=[]
    all_video_names = []
    all_video_frames = []
    for video_name in video_predictions.keys():
        # get only timesteps and predictions from video_predictions
        timesteps_with_predictions = video_predictions[video_name]
        timesteps_with_predictions = [(item[1], item[2]) for item in timesteps_with_predictions]
        # average predictions on timesteps
        current_timesteps, current_predictions = __average_predictions_on_timesteps(timesteps_with_predictions)
        # round timesteps one more time as preventive measure
        current_timesteps = np.round(current_timesteps, 2)
        # before interpolation, add the last timestep of the labels to the current_timesteps and duplicate the prediction for
        # that timestep
        if current_timesteps[-1] != dev_labels[video_name]['timesteps'].iloc[-1]:
            current_timesteps = np.append(current_timesteps, dev_labels[video_name]['timesteps'].iloc[-1])
            current_predictions = np.vstack((current_predictions, current_predictions[-1]))
        # interpolate predictions to 100 fps
        current_predictions, current_timesteps = __interpolate_to_100_fps(current_predictions, current_timesteps)
        # get timesteps of labels and labels
        video_labels_timesteps = dev_labels[video_name]['timesteps'].values
        if challenge == 'Exp':
            video_labels = dev_labels[video_name]['category'].values
        else:
            video_labels = dev_labels[video_name][['valence', 'arousal']].values
        # synchronize predictions with labels
        current_predictions, current_timesteps, video_labels, video_labels_timesteps = \
            __synchronize_predictions_with_ground_truth(current_predictions, current_timesteps, video_labels, video_labels_timesteps)
        # apply hamming window
        current_predictions = __apply_hamming_smoothing(current_predictions, smoothing_window_size=video_to_fps[video_name]//2)
        # check if the number of predictions corresponds to the number of labels+
        assert len(current_predictions) == len(video_labels), f'Number of predictions ({len(current_predictions)}) does not correspond to the number of labels ({len(video_labels)})'
        # append to the all_predictions
        all_predictions.append(current_predictions)
        all_timesteps.append(current_timesteps)
        all_labels.append(video_labels)
        all_labels_timesteps.append(video_labels_timesteps)
        all_video_names.append([video_name] * len(video_labels))
        all_video_frames.append(np.arange(0, len(video_labels)))

    # concatenate all_predictions and all_timesteps
    all_predictions = np.concatenate(all_predictions, axis=0)
    all_timesteps = np.concatenate(all_timesteps)
    all_labels = np.concatenate(all_labels)
    all_labels_timesteps = np.concatenate(all_labels_timesteps)
    all_video_names = np.concatenate(all_video_names)
    all_video_frames = np.concatenate(all_video_frames)

    return all_labels, all_predictions, zip(all_video_names, all_video_frames)

