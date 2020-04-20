import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F 

from RelationalModule import Networks as net
from pysc2.lib import actions

_NO_OP = actions.FUNCTIONS.no_op.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_MOVE_SCREEN = actions.FUNCTIONS.Attack_screen.id

debug = False

### OHE Control agent ###

class OheActor(nn.Module):
    """
    Use OheNet followed by a linear layer with log-softmax activation.
    """
    def __init__(self, action_space, map_size, **net_args):
        """
        Parameters
        ----------
        action_space: int
            Number of (discrete) possible actions to take
        map_size: int
            If input is (batch_dim, n_channels, linear_size, linear_size), 
            then map_size = linear_size - 2
        **net_args: dict (optional)
            Dictionary of {'key':value} pairs valid for OheNet
        """
        super(OheActor, self).__init__()
        
        self.action_dict = {0:_NO_OP, 1:_SELECT_ARMY, 2:_MOVE_SCREEN}
        self.net = net.OheNet(map_size, **net_args)
        self.linear = nn.Linear(self.net.n_features, action_space)
        
    def forward(self, state, available_actions):
        out = self.net(state)
        logits = self.linear(out)
        if debug: print("logits: ", logits)
        mask = self.get_action_mask(available_actions)
        if debug: print("mask: ", mask)
        logits[:,mask] = torch.tensor(np.NINF)
        if debug: print("logits (after mask): ", logits)
        log_probs = F.log_softmax(logits, dim=-1)
        return log_probs
        
    def get_action_mask(self, available_actions):
        action_mask = ~np.array([self.action_dict[i] in available_actions for i in self.action_dict.keys()])
        return action_mask
    
class OheBasicCritic(nn.Module):
    """
    Use OheNet followed by a linear layer with a scalar output without
    activation function.
    """
    
    def __init__(self, map_size, **net_args):
        """
        Parameters
        ----------
        map_size: int
            If input is (batch_dim, n_channels, linear_size, linear_size), 
            then map_size = linear_size - 2
        **net_args: dict (optional)
            Dictionary of {'key':value} pairs valid for OheNet
        """
        super(OheBasicCritic, self).__init__()
        self.net = net.OheNet(map_size, **net_args)
        self.linear = nn.Linear(self.net.n_features, 1)
    
    def forward(self, state):
        out = self.net(state)
        V = self.linear(out)
        return V
    
class OheCritic(nn.Module):
    """
    Implements a generic critic that can have 2 independent networks is twin=True. 
    """
    def __init__(self, map_size, twin=True, target=False, **net_args):
        """
        Parameters
        ----------
        map_size: int
            If input is (batch_dim, n_channels, linear_size, linear_size), 
            then map_size = linear_size - 2
        twin: bool (default True)
            If True uses 2 critics
        target: bool (default False)
            If True, returns the minimum between the two critic's predictions
        **net_args: dict (optional)
            Dictionary of {'key':value} pairs valid for OheNet
        """
        super(OheCritic, self).__init__()
        
        self.twin = twin
        self.target = target
        
        if twin:
            self.net1 = OheBasicCritic(map_size, **net_args)
            self.net2 = OheBasicCritic(map_size, **net_args)
        else:
            self.net = OheBasicCritic(map_size, **net_args)
        
    def forward(self, state):
        if self.twin:
            v1 = self.net1(state)
            v2 = self.net2(state)
            if self.target:
                v = torch.min(v1, v2) 
            else:
                return v1, v2
        else:
            v = self.net(state)
            
        return v               
        
        
        
        
        
        
        
        
        
        
    
