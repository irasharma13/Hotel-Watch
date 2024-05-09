import matplotlib.pyplot as plt
import torch
import torchvision
import os
from torch import nn
import pandas as pd
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from helper_functions import set_seeds
from torchinfo import summary  #need to pip install
import engine

device = "cuda" if torch.cuda.is_available() else "cpu"
print('DEVICE NAME: ',device)

# 1. Get pretrained weights for ViT-Base
pretrained_vit_weights = torchvision.models.ViT_B_16_Weights.DEFAULT
# 2. Setup a ViT model instance with pretrained weights
pretrained_vit = torchvision.models.vit_b_16(weights=pretrained_vit_weights).to(device)

# 3. Freeze the base parameters
for parameter in pretrained_vit.parameters():
    parameter.requires_grad = False
    
# 4. Change the classifier head 
# class_names = ['daisy','dandelion']
df1 = pd.read_csv('/home/016690830/masterproj/notebooks/data_preprocessing/updated_hotel_to_imagecount_mapping.csv')
class_names = df1['hotel_id']

set_seeds()
pretrained_vit.heads = nn.Linear(in_features=768, out_features=len(class_names)).to(device)

# Setup directory paths to train and test images
train_dir = '../../data/final/train_images'
val_dir = '../../data/final/validation_images'

# Get automatic transforms from pretrained ViT weights
pretrained_vit_transforms = pretrained_vit_weights.transforms()
print(pretrained_vit_transforms)


NUM_WORKERS = os.cpu_count()

def create_dataloaders(
    train_dir: str, 
    test_dir: str, 
    transform: transforms.Compose, 
    batch_size: int, 
    num_workers: int=NUM_WORKERS
):

  # Use ImageFolder to create dataset(s)
  train_data = datasets.ImageFolder(train_dir, transform=transform)
  test_data = datasets.ImageFolder(test_dir, transform=transform)

  # Get class names
  class_names = train_data.classes

  # Turn images into data loaders
  train_dataloader = DataLoader(
      train_data,
      batch_size=batch_size,
      shuffle=True,
      num_workers=num_workers,
      pin_memory=True,
  )
  test_dataloader = DataLoader(
      test_data,
      batch_size=batch_size,
      shuffle=False,
      num_workers=num_workers,
      pin_memory=True,
  )

  return train_dataloader, test_dataloader, class_names

  # Setup dataloaders
train_dataloader_pretrained, test_dataloader_pretrained, class_names = create_dataloaders(train_dir=train_dir,
                                                                                                     test_dir=val_dir,
                                                                                                     transform=pretrained_vit_transforms,
                                                                                                     batch_size=32) # Could increase if we had more samples, such as here: https://arxiv.org/abs/2205.01580 (there are other improvements there too...)

# Create optimizer and loss function
optimizer = torch.optim.Adam(params=pretrained_vit.parameters(), 
                             lr=1e-3)
loss_fn = torch.nn.CrossEntropyLoss()

# Train the classifier head of the pretrained ViT feature extractor model
set_seeds()
# Define the checkpoint path and start_epoch
checkpoint_path = "checkpoint path " 
start_epoch = 10  # Start from epoch 10

# Call the resume_train function
results = engine.resume_train(model=pretrained_vit, 
                        train_dataloader=train_dataloader_pretrained, 
                        test_dataloader=test_dataloader_pretrained, 
                        optimizer=optimizer, 
                        loss_fn=loss_fn, 
                        epochs=5, 
                        device=device, 
                        checkpoint_path=checkpoint_path, 
                        start_epoch=start_epoch)

# Print the results
print(results)