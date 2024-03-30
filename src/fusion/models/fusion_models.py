import torch
from torch import nn

from fusion.models.layers_utils import PositionalEncoding, MultiHeadAttention


class final_fusion_model_v1(nn.Module):


    def __init__(self, audio_shape=(4, 1024), video_shape=(20, 256), num_classes=None, num_regression_neurons=None):
        super(final_fusion_model_v1, self).__init__()
        self.audio_shape = audio_shape
        self.video_shape = video_shape

        self.audio_feature_down_sampling = nn.Sequential(
            nn.Linear(audio_shape[1], 256),
            nn.GELU(),
        )

        self.positional_encoding_audio = PositionalEncoding(d_model=256, dropout=0.1, max_len=audio_shape[0])
        self.positional_encoding_video = PositionalEncoding(d_model=256, dropout=0.1, max_len=video_shape[0])

        self.fusion_layer_1 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                      num_heads=16, dropout = 0.1,
                                                      masking_strategy= 'padding')
        self.batch_norm_1 = nn.BatchNorm1d(256)
        self.fusion_layer_2 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                        num_heads=16, dropout = 0.1,
                                                        masking_strategy= 'padding')
        self.batch_norm_2 = nn.BatchNorm1d(256)

        if num_classes is not None:
            self.output_layer = nn.Linear(256, num_classes)
        elif num_regression_neurons is not None:
            self.output_layer = nn.Linear(256, num_regression_neurons)



    def forward(self, features):
        audio, video = features # audio (batch_size, 4, 1024), video (batch_size, 20, 256)
        # pass audio through GRU
        audio = self.audio_feature_down_sampling(audio)
        # add positional encodings to audio and video
        audio = self.positional_encoding_audio(audio)
        video = self.positional_encoding_video(video)
        # pad audio to the same length as video
        audio = self.__pad(audio, self.video_shape[0])
        # generate mask for audio
        audio_mask = self.__generate_mask(audio)
        # pass through fusion layer
        fused_features = self.fusion_layer_1(queries = video, keys=audio, values = audio, mask=audio_mask)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_1(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # second fusion
        fused_features = self.positional_encoding_video(fused_features)
        fused_features = self.fusion_layer_2(queries = fused_features, keys=audio, values = audio, mask=audio_mask)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_2(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # pass through output layer
        output = self.output_layer(fused_features)
        return output

    def __pad(self, sequence, needed_length):
        # (batch_size, seq_len, input_dim)
        if sequence.shape[1] > needed_length:
            return sequence[:needed_length]
        else:
            return torch.cat([sequence, torch.zeros(sequence.shape[0], needed_length - sequence.shape[1], sequence.shape[2], device=sequence.device)], dim=1)

    def __generate_mask(self, sequence):
        # generates mask for the values that are all ZERO across one timestep (dimension with idx 1)
        return ~(sequence.sum(dim=2) == 0)





class final_fusion_model_v2(nn.Module):

    def __init__(self, audio_shape=(4, 1024), video_shape=(20, 256), num_classes=None, num_regression_neurons=None):
        super(final_fusion_model_v2, self).__init__()
        self.audio_shape = audio_shape
        self.video_shape = video_shape

        self.audio_feature_down_sampling = nn.Sequential(
            nn.Linear(audio_shape[1], 256),
            nn.GELU(),
        )

        self.positional_encoding_audio = PositionalEncoding(d_model=256, dropout=0.1, max_len=audio_shape[0])
        self.positional_encoding_video = PositionalEncoding(d_model=256, dropout=0.1, max_len=video_shape[0])

        self.fusion_layer_1 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                 num_heads=16, dropout=0.1,
                                                 masking_strategy='padding')

        self.fusion_layer_2 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                 num_heads=16, dropout=0.1,
                                                 masking_strategy='padding')

        self.fusion_layer_3 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                 num_heads=16, dropout=0.1,
                                                 masking_strategy='padding')

        self.fusion_layer_4 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                 num_heads=16, dropout=0.1,
                                                 masking_strategy='padding')

        self.batch_norm_1 = nn.BatchNorm1d(256)
        self.batch_norm_2 = nn.BatchNorm1d(256)
        self.batch_norm_3 = nn.BatchNorm1d(256)
        self.batch_norm_4 = nn.BatchNorm1d(256)

        if num_classes is not None:
            self.output_layer = nn.Linear(256, num_classes)
        elif num_regression_neurons is not None:
            self.output_layer = nn.Linear(256, num_regression_neurons)

    def forward(self, features):
        audio, video = features  # audio (batch_size, 4, 1024), video (batch_size, 20, 256)
        # pass audio through GRU
        audio = self.audio_feature_down_sampling(audio)
        # add positional encodings to audio and video
        audio = self.positional_encoding_audio(audio)
        video = self.positional_encoding_video(video)
        # pad audio to the same length as video
        audio = self.__pad(audio, self.video_shape[0])
        # generate mask for audio
        audio_mask = self.__generate_mask(audio)
        # pass through fusion layer
        fused_features = self.fusion_layer_1(queries=video, keys=audio, values=audio, mask=audio_mask)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_1(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # second fusion
        fused_features = self.positional_encoding_video(fused_features)
        fused_features = self.fusion_layer_2(queries=fused_features, keys=audio, values=audio, mask=audio_mask)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_2(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # third fusion
        fused_features = self.positional_encoding_video(fused_features)
        fused_features = self.fusion_layer_3(queries=fused_features, keys=video, values=video)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_3(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # fourth fusion
        fused_features = self.positional_encoding_video(fused_features)
        fused_features = self.fusion_layer_4(queries=fused_features, keys=video, values=video)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_4(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # pass through output layer
        output = self.output_layer(fused_features)
        return output

    def __pad(self, sequence, needed_length):
        # (batch_size, seq_len, input_dim)
        if sequence.shape[1] > needed_length:
            return sequence[:needed_length]
        else:
            return torch.cat([sequence,
                              torch.zeros(sequence.shape[0], needed_length - sequence.shape[1], sequence.shape[2],
                                          device=sequence.device)], dim=1)

    def __generate_mask(self, sequence):
        # generates mask for the values that are all ZERO across one timestep (dimension with idx 1)
        return ~(sequence.sum(dim=2) == 0)


class final_fusion_model_v3(nn.Module):

    def __init__(self, audio_shape=(4, 1024), video_shape=(20, 256), num_classes=None, num_regression_neurons=None):
        super(final_fusion_model_v3, self).__init__()
        self.audio_shape = audio_shape
        self.video_shape = video_shape

        self.audio_feature_downsampling = self.audio_feature_down_sampling = nn.Sequential(
            nn.Linear(audio_shape[1], 256),
            nn.GELU(),
        )
        self.video_cnn_downsampling = nn.Conv1d(in_channels=video_shape[-1], out_channels=video_shape[-1],
                                                kernel_size=video_shape[0]//4, stride=video_shape[0]//4)

        self.positional_encoding_audio = PositionalEncoding(d_model=256, dropout=0.1, max_len=audio_shape[0])
        self.positional_encoding_video = PositionalEncoding(d_model=256, dropout=0.1, max_len=audio_shape[0])

        self.fusion_layer_1 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                      num_heads=16, dropout = 0.1,
                                                      masking_strategy= 'padding')
        self.batch_norm_1 = nn.BatchNorm1d(256)
        self.fusion_layer_2 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                        num_heads=16, dropout = 0.1,
                                                        masking_strategy= 'padding')
        self.batch_norm_2 = nn.BatchNorm1d(256)

        if num_classes is not None:
            self.output_layer = nn.Linear(256, num_classes)
        elif num_regression_neurons is not None:
            self.output_layer = nn.Linear(256, num_regression_neurons)


    def forward(self, features):
        audio, video = features # audio (batch_size, 4, 1024), video (batch_size, 20, 256)
        # pass audio through GRU
        audio = self.audio_feature_downsampling(audio)
        # downsample video
        video = video.permute(0, 2, 1)
        video = self.video_cnn_downsampling(video)
        video = video.permute(0, 2, 1)
        # add positional encodings to audio and video
        audio = self.positional_encoding_audio(audio)
        video = self.positional_encoding_video(video)
        # pass through fusion layer
        fused_features = self.fusion_layer_1(queries = video, keys=audio, values = audio)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_1(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # second fusion
        fused_features = self.positional_encoding_video(fused_features)
        fused_features = self.fusion_layer_2(queries = fused_features, keys=video, values = video)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_2(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # pass through output layer
        output = self.output_layer(fused_features)
        # the output has shape (batch_size, 4, num_classes/num_regression_neurons)
        # we need to expand 4 timesteps to 20 in a way that one timestep will repeat itself 5 times
        output = torch.concat([output[:,i,:].unsqueeze(1).repeat(1, 5, 1) for i in range(4)], dim=1)
        return output


class final_fusion_model_v4(nn.Module):

    def __init__(self, audio_shape=(4, 1024), video_shape=(20, 256), num_classes=None, num_regression_neurons=None):
        super(final_fusion_model_v4, self).__init__()
        self.audio_shape = audio_shape
        self.video_shape = video_shape

        self.audio_pooling = nn.AdaptiveAvgPool1d(1)
        self.video_pooling = nn.AdaptiveAvgPool1d(1)
        self.embeddings_layer = nn.Sequential(
            nn.Linear(audio_shape[1] + video_shape[1], 256),
            nn.GELU(),
        )

        if num_classes is not None:
            self.output_layer = nn.Linear(256, num_classes)
        elif num_regression_neurons is not None:
            self.output_layer = nn.Linear(256, num_regression_neurons)



    def forward(self, features):
        audio, video = features # audio (batch_size, 4, 1024), video (batch_size, 20, 256)
        # pass audio through pooling
        audio = audio.permute(0, 2, 1)
        audio = self.audio_pooling(audio)
        audio = audio.squeeze(-1)
        # pass video through pooling
        video = video.permute(0, 2, 1)
        video = self.video_pooling(video)
        video = video.squeeze(-1)
        # concat audio and video
        fused_features = torch.cat([audio, video], dim=-1)
        # pass through embeddings layer
        fused_features = self.embeddings_layer(fused_features)
        # pass through output layer
        output = self.output_layer(fused_features)
        # add dimension for time and copy the same output for all timesteps (20)
        output = output.unsqueeze(1).repeat(1, 20, 1)
        return output

class final_fusion_model_v5(nn.Module):

    def __init__(self, audio_shape=(4, 1024), video_shape=(20, 256), num_classes=None, num_regression_neurons=None):
        super(final_fusion_model_v5, self).__init__()
        self.audio_shape = audio_shape
        self.video_shape = video_shape

        self.audio_feature_downsampling = self.audio_feature_down_sampling = nn.Sequential(
            nn.Linear(audio_shape[1], 256),
            nn.GELU(),
        )
        self.video_cnn_downsampling = nn.Conv1d(in_channels=video_shape[-1], out_channels=video_shape[-1],
                                                kernel_size=video_shape[0]//4, stride=video_shape[0]//4)

        self.positional_encoding_audio = PositionalEncoding(d_model=256, dropout=0.1, max_len=audio_shape[0])
        self.positional_encoding_video = PositionalEncoding(d_model=256, dropout=0.1, max_len=audio_shape[0])

        self.fusion_layer_1 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                      num_heads=16, dropout = 0.1,
                                                      masking_strategy= 'padding')
        self.batch_norm_1 = nn.BatchNorm1d(256)
        self.fusion_layer_2 = MultiHeadAttention(input_dim_query=256, input_dim_keys=256, input_dim_values=256,
                                                        num_heads=16, dropout = 0.1,
                                                        masking_strategy= 'padding')
        self.batch_norm_2 = nn.BatchNorm1d(256)

        if num_classes is not None:
            self.output_layer = nn.Linear(256, num_classes)
        elif num_regression_neurons is not None:
            self.output_layer = nn.Linear(256, num_regression_neurons)


    def forward(self, features):
        audio, video = features # audio (batch_size, 4, 1024), video (batch_size, 20, 256)
        # pass audio through GRU
        audio = self.audio_feature_downsampling(audio)
        # downsample video
        video = video.permute(0, 2, 1)
        video = self.video_cnn_downsampling(video)
        video = video.permute(0, 2, 1)
        # add positional encodings to audio and video
        audio = self.positional_encoding_audio(audio)
        video = self.positional_encoding_video(video)
        # concatenate audio and video
        fused_features = torch.cat([audio, video], dim=1)
        # pass through fusion layer
        fused_features = self.fusion_layer_1(queries = fused_features, keys=fused_features, values = fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_1(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # second fusion
        fused_features = self.fusion_layer_2(queries = fused_features, keys=fused_features, values = fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        fused_features = self.batch_norm_2(fused_features)
        fused_features = fused_features.permute(0, 2, 1)
        # pass through output layer
        output = self.output_layer(fused_features)
        # the output has shape (batch_size, 4, num_classes/num_regression_neurons)
        # we need to expand 4 timesteps to 20 in a way that one timestep will repeat itself 5 times
        output = torch.concat([output[:,i,:].unsqueeze(1).repeat(1, 5, 1) for i in range(4)], dim=1)
        return output



if __name__ == "__main__":
    # create model
    model = final_fusion_model_v5(num_classes=8)
    # create some dummy data
    audio = torch.randn(8, 4, 1024)  # [batch_size, seq_len, input_dim]
    video = torch.randn(8, 20, 256)  # [batch_size, seq_len, input_dim]
    # forward pass
    output = model((audio, video))
    print(output.shape)  # torch.Size([8, 20, 8])