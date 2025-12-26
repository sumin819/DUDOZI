# steering_model.py
import torch
import torchvision
import torchvision.transforms as transforms
import PIL.Image
import numpy as np

device = torch.device('cuda')

model = torchvision.models.resnet18(pretrained=False)
model.fc = torch.nn.Linear(512, 2)
model.load_state_dict(torch.load('best_steering_model_xy_test.pth'))
model = model.to(device).eval().half()

mean = torch.Tensor([0.485, 0.456, 0.406]).cuda().half()
std = torch.Tensor([0.229, 0.224, 0.225]).cuda().half()

def preprocess(image):
    image = PIL.Image.fromarray(image)
    image = transforms.functional.to_tensor(image).to(device).half()
    image.sub_(mean[:, None, None]).div_(std[:, None, None])
    return image[None, ...]

def infer_xy(frame):
    with torch.no_grad():
        xy = model(preprocess(frame)).float().cpu().numpy().flatten()
    return xy[0], xy[1]
