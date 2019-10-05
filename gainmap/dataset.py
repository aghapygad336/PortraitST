from __future__ import print_function
import torch.utils.data as data
import os
import torch
import random
import numpy as np
from torch.autograd import Variable
import torchvision.transforms as transforms
from PIL import Image
import cv2

IMG_EXTENSIONS = [
    '.jpg', '.JPG', '.jpeg', '.JPEG',
    '.png', '.PNG', '.bmp', '.BMP',
]

# denormalize
def de_norm():
    invTrans = transforms.Compose([ transforms.Normalize(mean = [ 0., 0., 0. ],
                                                     std = [ 1/0.229, 1/0.224, 1/0.225 ]),
                                transforms.Normalize(mean = [ -0.485, -0.456, -0.406 ],
                                                     std = [ 1., 1., 1. ]),
                               ])
    return invTrans

# normalization step before puts in VGG.
def make_trans():
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
    tensorize = transforms.ToTensor()
    trans = transforms.Compose([tensorize, normalize])
    return trans

# test file by extension
def is_image_file(filename):
    return any(filename.endswith(extension) for extension in IMG_EXTENSIONS)

# find all image files and store paths as a list.
def make_dataset(dir):
    images = []
    print(dir)
    assert os.path.isdir(dir), '%s is not a valid directory' % dir

    for root, _, fnames in sorted(os.walk(dir)):
        for fname in fnames:
            if is_image_file(fname):
                path = os.path.join(root, fname)
                images.append(path)
    images.sort()
    return images


# The Style-Transfer Dataset.
# mode = Paired: ONE style example with ONE paired inputs;
#        Others: ONE style example with MULTIPLE inputs;
class ST_dataset(data.Dataset):
    def __init__(self, root, name='testing', mode='paired'):
        self.feat = make_dataset(os.path.join(root,name,'style'))
        self.input = make_dataset(os.path.join(root,name,'input'))
        self.mode = mode
        self.name = name
        self.trans = make_trans()

    def __getitem__(self, index):
        if self.mode == 'paired':
            return [self.get_image(self.feat[index%len(self)], mode='style'),
             self.get_image(self.input[index%1], mode='input')]
        else:
            return [self.get_image(self.feat[0], mode='style'),
             self.get_image(self.input[index%len(self)], mode='input')]

    def __len__(self):
        return len(self.feat)

    # open and get a image tensor.
    def get_image(self, filename, mode='input'):
        src = cv2.cvtColor(cv2.imread(filename), cv2.COLOR_BGR2RGB)
        src = cv2.resize(src, (500, 660))
        img = src.astype(np.float32)
        #tensor = torch.from_numpy(img.transpose(2,0,1))
        tensor = self.trans(img)
        if 'input' in mode:
            img = Variable(tensor, requires_grad=True)#, device='cuda')
        elif 'style' in mode:
            img = Variable(tensor, requires_grad=False)
        return img

# Dataset for reconstruction network.
class RC_dataset(data.Dataset):
    def __init__(self, root, name='train', mode='unpaired'):
        self.feat = make_dataset(os.path.join(root,'styles'))
        self.input = make_dataset(os.path.join(root,'ffhq'))
        self.mode = mode
        self.name = name
        self.trans = make_trans()

    def __getitem__(self, index):
        if 'train' in self.name:
            style = self.feat[(index)%(len(self.feat)-100)]
            #style = self.feat[random.randint(0, len(self.feat)-100)]
            face = self.input[random.randint(0, 67000)]
        elif 'test' in self.name:
            style = self.feat[random.randint(len(self.feat)-99, len(self.feat)-1)]
            face = self.input[random.randint(68000, 69000)]
        #print(face, style)
        return [self.get_image(face, 'input'),
                self.get_image(style, 'style')]

    def get_image(self, filename, mode):
        src = cv2.cvtColor(cv2.imread(filename), cv2.COLOR_BGR2RGB)
        src = cv2.resize(src, (512, 512))
        img = src.astype(np.float32)

        tensor = self.trans(img)
        if 'input' in mode:
            img = Variable(tensor, requires_grad=False)
        elif 'style' in mode:
            img = Variable(tensor, requires_grad=False)
        return img

    def __len__(self):
        if 'train' in self.name: 
            return len(self.feat)-100
        else:
            return 10





