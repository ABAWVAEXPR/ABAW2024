# SUN Team's Contribution to ABAW 2024 Competition: Audio-visual Valence-Arousal Estimation and Expression Recognition 

As emotions play a central role in human communication, automatic emotion recognition has attracted increasing attention in the last two decades. While multimodal systems enjoy high performances on lab-controlled data, they are still far from providing ecological validity on non-lab-controlled, namely ‘in-the-wild’ data. This work investigates audiovisual deep learning approaches for emotion recognition in-the-wild problem. We particularly explore the effectiveness of architectures based on fine-tuned Convolutional Neural Networks (CNN) and Public Dimensional Emotion Model (PDEM), for video and audio modality, respectively. We compare alternative temporal modeling and fusion strategies using the embeddings from these multi-stage trained modality-specific Deep Neural Networks (DNN). We report results on the AffWild2 dataset under Affective Behavior Analysis in-the-Wild 2024 (ABAW’24) challenge protocol


The architectures of all emotion recognition models used in this work are presented below.

 ![The architecture of Kernel ELM based dynamic emotion recognition model.](https://github.com/ABAWVAEXPR/ABAW2024/blob/main/figures/KELM_architecture.png)
&NewLine;
&NewLine;
 
 ![The neural network architecture of modified frame-level FER models. n -- number of neurons, 8 for classification task and 2 for regression task. After generation of predictions, a softmax or tanh activation function is applied depending on the task type.](https://github.com/ABAWVAEXPR/ABAW2024/blob/main/figures/efficientNet_modifications_static.png)
&NewLine;
&NewLine;
 
 ![Pipeline and architecture of the transformer-based sequence to one video emotion recognition model. W -- the temporal window size (in the number of frames), N -- the number of neurons in the decision-making head (either 8 for classification or 2 for regression task).](https://github.com/ABAWVAEXPR/ABAW2024/blob/main/figures/facial_sequence_to_one_model.png)



Model weights are available at [Google Drive](https://drive.google.com/drive/folders/12LLx9DiEJSlnzgL745m9z_XAz1Rw_Vz6?usp=sharing).
