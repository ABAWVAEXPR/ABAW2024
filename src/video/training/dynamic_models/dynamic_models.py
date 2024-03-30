from typing import Tuple, Optional

import torch

from pytorch_utils.layers.attention_layers import Transformer_layer

class UniModalTemporalModel_v1(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:int, num_regression_neurons:int):
        super(UniModalTemporalModel_v1, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.first_temporal_part = torch.nn.ModuleList()
        self.second_temporal_part = torch.nn.ModuleList()
        self.third_temporal_part = torch.nn.ModuleList()
        # first part of the model
        self.first_temporal_part.append(Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True))
        self.first_temporal_part.append(Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True))
        # two more transformer layers
        self.second_temporal_part.append(Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True))
        self.second_temporal_part.append(Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True))
        # two more transformer layers
        self.third_temporal_part.append(Transformer_layer(input_dim=self.num_features, num_heads=4, dropout=0.1, positional_encoding=True))
        self.third_temporal_part.append(Transformer_layer(input_dim=self.num_features, num_heads=4, dropout=0.1, positional_encoding=True))


    def forward(self, x):
        # first temporal part
        for layer in self.first_temporal_part:
            x = layer(x, x, x)
        # second temporal part
        for layer in self.second_temporal_part:
            x = layer(x, x, x)
        # third temporal part
        for layer in self.third_temporal_part:
            x = layer(x, x, x)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output





class UniModalTemporalModel_v2(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:int, num_regression_neurons:int):
        super(UniModalTemporalModel_v2, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features//4, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.first_temporal_part = torch.nn.ModuleList()
        self.second_temporal_part = torch.nn.ModuleList()
        self.third_temporal_part = torch.nn.ModuleList()
        # first part of the model
        self.first_temporal_part.append(Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True))
        # reduction of feature dimension by 2
        self.feature_reduction_1 = torch.nn.Sequential(
            torch.nn.Conv1d(in_channels=self.num_features, out_channels=self.num_features //2, kernel_size=1, stride=1),
            torch.nn.BatchNorm1d(num_features=self.num_features // 2),
            torch.nn.GELU(),
            torch.nn.Dropout(p=0.1),
        )
        # two more transformer layers
        self.second_temporal_part.append(Transformer_layer(input_dim=self.num_features//2, num_heads=8, dropout=0.1, positional_encoding=True))

        self.feature_reduction_2 = torch.nn.Sequential(
            torch.nn.Conv1d(in_channels=self.num_features//2, out_channels=self.num_features // 4, kernel_size=1, stride=1),
            torch.nn.BatchNorm1d(num_features=self.num_features // 4),
            torch.nn.GELU(),
            torch.nn.Dropout(p=0.1),
        )
        # two more transformer layers
        self.third_temporal_part.append(Transformer_layer(input_dim=self.num_features//4, num_heads=4, dropout=0.1, positional_encoding=True))


    def forward(self, x):
        # first temporal part
        for layer in self.first_temporal_part:
            x = layer(x, x, x)
        # reduction
        x = x.permute(0, 2, 1)
        x = self.feature_reduction_1(x)
        x = x.permute(0, 2, 1)
        # second temporal part
        for layer in self.second_temporal_part:
            x = layer(x, x, x)
        # reduction
        x = x.permute(0, 2, 1)
        x = self.feature_reduction_2(x)
        x = x.permute(0, 2, 1)
        # third temporal part
        for layer in self.third_temporal_part:
            x = layer(x, x, x)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output

class UniModalTemporalModel_v3(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:int, num_regression_neurons:int):
        super(UniModalTemporalModel_v3, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.start_batch_norm = torch.nn.BatchNorm1d(num_features=self.num_features)
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.first_transformer = Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True)
        self.second_transformer = Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True)
        self.third_transformer = Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True)


    def forward(self, x):
        # start batch norm
        x = x.permute(0, 2, 1)
        x = self.start_batch_norm(x)
        x = x.permute(0, 2, 1)
        # temporal part
        x = self.first_transformer(x, x, x)
        x = self.second_transformer(x, x, x)
        x = self.third_transformer(x, x, x)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output



class UniModalTemporalModel_v4(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:Optional[int]=None, num_regression_neurons:Optional[int]=None):
        super(UniModalTemporalModel_v4, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.temporal_part = torch.nn.GRU(input_size=self.num_features, hidden_size=self.num_features, num_layers=2,
                                      batch_first=True, dropout=0.1, bidirectional=False)


    def forward(self, x):
        # temporal part
        x, _ = self.temporal_part(x)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output


class UniModalTemporalModel_v5(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:int, num_regression_neurons:int):
        super(UniModalTemporalModel_v5, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.first_transformer = Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True)


    def forward(self, x):
        # temporal part
        x = self.first_transformer(x, x, x)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output

class UniModalTemporalModel_v6_1_fps(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:int, num_regression_neurons:int):
        super(UniModalTemporalModel_v6_1_fps, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.transformer = Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True)
        # layer to downgrade the number of timesteps to 1 fps (//5)
        self.downgrader = torch.nn.Sequential(
            torch.nn.Linear(in_features=self.num_timesteps, out_features=self.num_timesteps//5),
            torch.nn.GELU(),
            torch.nn.Dropout(p=0.1),
        )


    def forward(self, x):
        # temporal part
        x = self.transformer(x, x, x) # -> (batch_size, num_timesteps, num_features)
        # downgrading the number of timesteps
        x = x.permute(0, 2, 1)
        x = self.downgrader(x)
        x = x.permute(0, 2, 1)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output

class UniModalTemporalModel_v7_1_fps(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:int, num_regression_neurons:int):
        super(UniModalTemporalModel_v7_1_fps, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.transformer = Transformer_layer(input_dim=self.num_features, num_heads=8, dropout=0.1, positional_encoding=True)
        # layer to downgrade the number of timesteps to 1 fps (//5)
        self.downgrader = torch.nn.Sequential(
            torch.nn.Conv1d(in_channels=self.num_features, out_channels=self.num_features, kernel_size=5, stride=5),
            torch.nn.GELU(),
            torch.nn.Dropout(p=0.1),
        )


    def forward(self, x):
        # temporal part
        x = self.transformer(x, x, x) # -> (batch_size, num_timesteps, num_features)
        # downgrading the number of timesteps
        x = x.permute(0, 2, 1)
        x = self.downgrader(x)
        x = x.permute(0, 2, 1)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output

class UniModalTemporalModel_v8_1_fps(torch.nn.Module):
    def __init__(self, input_shape:Tuple[int, int], num_classes:int, num_regression_neurons:int):
        super(UniModalTemporalModel_v8_1_fps, self).__init__()
        self.num_timesteps, self.num_features = input_shape # (num_time_steps, num_features)
        self.num_classes = num_classes
        self.num_regression_neurons = num_regression_neurons
        self.__initialize_temporal_part()

        if self.num_classes is not None:
            self.classifier = torch.nn.Linear(in_features=self.num_features, out_features=self.num_classes)
        if self.num_regression_neurons is not None:
            self.regressor = torch.nn.Sequential(
                torch.nn.Linear(in_features=self.num_features, out_features=self.num_regression_neurons),
                torch.nn.Tanh())


    def __initialize_temporal_part(self):
        # make the first part of the model as torch list
        self.gru = torch.nn.GRU(input_size=self.num_features, hidden_size=self.num_features, num_layers=2,
                                      batch_first=True, dropout=0.1, bidirectional=False)
        # layer to downgrade the number of timesteps to 1 fps (//5)
        self.downgrader = torch.nn.Sequential(
            torch.nn.Conv1d(in_channels=self.num_features, out_channels=self.num_features, kernel_size=5, stride=5),
            torch.nn.GELU(),
            torch.nn.Dropout(p=0.1),
        )


    def forward(self, x):
        # temporal part
        x, _ = self.gru(x) # -> (batch_size, num_timesteps, num_features)
        # downgrading the number of timesteps
        x = x.permute(0, 2, 1)
        x = self.downgrader(x)
        x = x.permute(0, 2, 1)
        # output
        if self.num_classes is not None:
            output = self.classifier(x)
            return output
        elif self.num_regression_neurons is not None:
            output = self.regressor(x)
            return output




if __name__ == "__main__":
    model = UniModalTemporalModel_v8_1_fps(input_shape=(20,256), num_classes=8, num_regression_neurons=2)
    print(model)
    x = torch.rand(32, 20, 256)
    print(model(x))
    import torchsummary
    torchsummary.summary(model, (20, 256), device='cpu')
