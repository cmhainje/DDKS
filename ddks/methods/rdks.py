from .ddks import ddKS
import torch
import warnings

#Radial method for calculating ddks
#Method should always = 'all' subsampling not supported

class rdKS(ddKS):
    def __init__(self, soft=False, T=0.1, method='all', n_test_points=10,
                 pts=None, norm=False, oneway=True):
        super().__init__(soft, T, method, n_test_points,
                 pts, norm, oneway)

    def setup(self, pred, true):
        #Set dimension with pred dataset
        self.d = pred.shape[1]
        return

    def calcD(self, pred, true):
        #Find corners in d-dimensions
        self.find_corners(pred, true)
        d_from_corner_p = self.get_d_from_corner(pred)
        d_from_corner_t = self.get_d_from_corner(true)
        os_pp = self.get_orthants_from_d(d_from_corner_p, d_from_corner_p)
        os_pt = self.get_orthants_from_d(d_from_corner_t, d_from_corner_p)
        D1 = self.max((os_pp/pred.shape[0] - os_pt/true.shape[0]).abs())
        if self.oneway:
            D = D1
        else:
            warnings.warn("Only Oneway implemented for rdks")
        if self.norm:
            D = D / float(pred.shape[0])
        return D
    def get_d_from_corner(self, x):
        _x = x.unsqueeze(-1).repeat(1,1,2**self.d)
        d = _x - self.corners
        d = torch.sqrt(torch.sum(torch.pow(d, 2.0), dim=1))
        return d

    def get_orthants_from_d(self, d, d_test):
        os = torch.empty((d.shape[0], 2**self.d))
        sorted_ds = d
        sorted_test_args = torch.empty((d_test.shape)).long()
        for i in range(2**self.d):
            sorted_ds[:, i], _ = torch.sort(d[:, i])
            _, sorted_test_args[:, i] = torch.sort(d_test[:, i])
        N = d.shape[0]
        for octant in range(2**self.d):
            test_point_index = 0
            point_index = 0
            while test_point_index < N:
                idx = sorted_test_args[test_point_index, octant]
                while sorted_ds[point_index, octant] < d_test[idx, octant] and point_index < N - 1:
                    point_index += 1
                os[idx, octant] = point_index
                test_point_index += 1
        return os
    def find_corners(self, x1, x2):
        '''
        Creates corners to calculate distance from 
        :param x1: data set 1
        :param x2: data set 2
        :return:
        '''
        cs = torch.empty((2**self.d,self.d))
        x1_min,_ = torch.min(x1,dim=0)
        x2_min,_ = torch.min(x2,dim=0)
        x1_max,_ = torch.max(x1,dim=0)
        x2_max,_ = torch.max(x1, dim=0)
        mins,_ = torch.stack((x1_min,x2_min)).min(dim=0)
        maxs,_ = torch.stack((x1_max, x2_max)).max(dim=0)
        for n in range(2**self.d):
            bs = format(n, f'0{self.d}b')
            cs[n,:] = torch.tensor([mins[i] if c == '0' else maxs[i] for i, c in enumerate(bs)])
        self.corners = cs.T.unsqueeze(0)