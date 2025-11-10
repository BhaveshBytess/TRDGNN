"""
Heterogeneous Graph Builder for Elliptic++ Dataset
E5 Milestone: Build PyG HeteroData with temporal constraints

Features:
- Load transaction and address nodes
- Load 4 edge types: tx-tx, addr-tx, tx-addr, addr-addr
- Preserve temporal information
- Create train/val/test splits
- TRD sampler compatible
"""

import pandas as pd
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Tuple, Optional
import json
from torch_geometric.data import HeteroData
from tqdm.auto import tqdm
import warnings
warnings.filterwarnings('ignore')


class HeteroGraphBuilder:
    """
    Build heterogeneous graph from Elliptic++ CSV files.
    
    Node Types:
        - transaction: Bitcoin transactions (203K nodes)
        - address: Bitcoin addresses/wallets (823K nodes)
    
    Edge Types:
        - (transaction, to, transaction): tx-to-tx flows
        - (address, to, transaction): addr sends to tx (input)
        - (transaction, to, address): tx pays to addr (output)
        - (address, to, address): addr-to-addr connections
    """
    
    def __init__(self, data_root: str, use_all_addresses: bool = False):
        """
        Args:
            data_root: Path to data directory
            use_all_addresses: If False, use top 100K addresses (MVP)
        """
        self.data_root = Path(data_root)
        self.use_all_addresses = use_all_addresses
        
        # Node mappings (original ID -> index)
        self.tx_id_to_idx = {}
        self.addr_id_to_idx = {}
        
        # Reverse mappings (index -> original ID)
        self.tx_idx_to_id = {}
        self.addr_idx_to_id = {}
        
        # Statistics
        self.stats = {}
        
        print(f"HeteroGraphBuilder initialized")
        print(f"   Data root: {self.data_root}")
        print(f"   Use all addresses: {self.use_all_addresses}")
    
    def load_transaction_nodes(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Load transaction nodes with features, labels, and timestamps.
        
        Returns:
            x: Feature matrix [N_tx, 93] (Local features only)
            y: Labels [N_tx] (1=illicit, 0=licit, -1=unknown)
            timestamps: Timestamps [N_tx]
        """
        print("\n Loading transaction nodes...")
        
        # Load features
        features_df = pd.read_csv(self.data_root / "txs_features.csv")
        classes_df = pd.read_csv(self.data_root / "txs_classes.csv")
        
        # Merge
        data_df = features_df.merge(classes_df, on='txId', how='left')
        
        # Create ID mapping
        tx_ids = data_df['txId'].values
        self.tx_id_to_idx = {tx_id: idx for idx, tx_id in enumerate(tx_ids)}
        self.tx_idx_to_id = {idx: tx_id for idx, tx_id in enumerate(tx_ids)}
        
        print(f"   Transactions: {len(tx_ids):,}")
        
        # Extract LOCAL features only (AF1-AF93)
        feature_cols = [col for col in data_df.columns 
                       if col not in ['txId', 'Time step', 'class']]
        
        # Filter to Local features (first 93)
        local_features = [col for col in feature_cols if 'Local' in col]
        if not local_features:
            local_features = feature_cols[:93]
        
        print(f"   Features: {len(local_features)} (Local only)")
        
        # Extract features
        x = torch.FloatTensor(data_df[local_features].values)
        x = torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Normalize
        x_mean = x.mean(dim=0)
        x_std = x.std(dim=0)
        x = (x - x_mean) / (x_std + 1e-8)
        x = torch.nan_to_num(x, nan=0.0)
        
        # Extract timestamps
        timestamps = torch.LongTensor(data_df['Time step'].values)
        
        # Extract labels (1=illicit, 2=licit, 3=unknown)
        # Convert to: 1=fraud, 0=legit, -1=unknown
        y_raw = data_df['class'].fillna(3).astype(int).values
        y = np.where(y_raw == 1, 1, np.where(y_raw == 2, 0, -1))
        y = torch.LongTensor(y)
        
        print(f"   Labeled: {(y >= 0).sum():,} / {len(y):,}")
        print(f"   Fraud: {(y == 1).sum():,}, Legit: {(y == 0).sum():,}")
        
        self.stats['num_transactions'] = len(tx_ids)
        self.stats['tx_features'] = x.shape[1]
        self.stats['tx_labeled'] = (y >= 0).sum().item()
        
        return x, y, timestamps
    
    def load_address_nodes(self, top_k: Optional[int] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Load address nodes with features, labels, and timestamps.
        
        Args:
            top_k: If provided, only load top K most active addresses
        
        Returns:
            x: Feature matrix [N_addr, 52]
            y: Labels [N_addr] (1=illicit, 0=licit, -1=unknown)
            timestamps: Timestamps [N_addr]
        """
        print("\n Loading address nodes...")
        
        # Use combined file if available (smaller memory footprint)
        combined_file = self.data_root / "wallets_features_classes_combined.csv"
        if combined_file.exists():
            print(f"   Using combined wallet file...")
            data_df = pd.read_csv(combined_file)
        else:
            # Load separately
            features_df = pd.read_csv(self.data_root / "wallets_features.csv")
            classes_df = pd.read_csv(self.data_root / "wallets_classes.csv")
            data_df = features_df.merge(classes_df, on='address', how='left')
        
        # If top_k specified, select most active addresses
        if top_k is not None and not self.use_all_addresses:
            data_df = data_df.nlargest(top_k, 'total_txs')
            print(f"   Selected top {top_k:,} most active addresses")
        
        # Create ID mapping
        addr_ids = data_df['address'].values
        self.addr_id_to_idx = {addr_id: idx for idx, addr_id in enumerate(addr_ids)}
        self.addr_idx_to_id = {idx: addr_id for idx, addr_id in enumerate(addr_ids)}
        
        print(f"   Addresses: {len(addr_ids):,}")
        
        # Extract features (exclude ID, timestamp, class)
        feature_cols = [col for col in data_df.columns 
                       if col not in ['address', 'Time step', 'class']]
        
        print(f"   Features: {len(feature_cols)}")
        
        # Extract features
        x = torch.FloatTensor(data_df[feature_cols].values)
        x = torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Normalize
        x_mean = x.mean(dim=0)
        x_std = x.std(dim=0)
        x = (x - x_mean) / (x_std + 1e-8)
        x = torch.nan_to_num(x, nan=0.0)
        
        # Extract timestamps
        timestamps = torch.LongTensor(data_df['Time step'].values)
        
        # Extract labels
        y_raw = data_df['class'].fillna(3).astype(int).values
        y = np.where(y_raw == 1, 1, np.where(y_raw == 2, 0, -1))
        y = torch.LongTensor(y)
        
        print(f"   Labeled: {(y >= 0).sum():,} / {len(y):,}")
        print(f"   Fraud: {(y == 1).sum():,}, Legit: {(y == 0).sum():,}")
        
        self.stats['num_addresses'] = len(addr_ids)
        self.stats['addr_features'] = x.shape[1]
        self.stats['addr_labeled'] = (y >= 0).sum().item()
        
        return x, y, timestamps
    
    def load_edges(self, edge_type: str) -> torch.Tensor:
        """
        Load edges for a specific type.
        
        Args:
            edge_type: One of ['tx-tx', 'addr-tx', 'tx-addr', 'addr-addr']
        
        Returns:
            edge_index: [2, E] tensor of edge indices
        """
        file_map = {
            'tx-tx': 'txs_edgelist.csv',
            'addr-tx': 'AddrTx_edgelist.csv',
            'tx-addr': 'TxAddr_edgelist.csv',
            'addr-addr': 'AddrAddr_edgelist.csv'
        }
        
        if edge_type not in file_map:
            raise ValueError(f"Unknown edge type: {edge_type}")
        
        print(f"\n Loading {edge_type} edges...")
        
        edges_df = pd.read_csv(self.data_root / file_map[edge_type])
        
        # Get column names (may vary)
        cols = list(edges_df.columns)
        src_col, dst_col = cols[0], cols[1]
        
        # Map to indices based on edge type
        if edge_type == 'tx-tx':
            # Both are transaction IDs
            valid = (edges_df[src_col].isin(self.tx_id_to_idx) & 
                    edges_df[dst_col].isin(self.tx_id_to_idx))
            src_idx = edges_df.loc[valid, src_col].map(self.tx_id_to_idx).values
            dst_idx = edges_df.loc[valid, dst_col].map(self.tx_id_to_idx).values
            
        elif edge_type == 'addr-tx':
            # Source is address, dest is transaction
            valid = (edges_df[src_col].isin(self.addr_id_to_idx) & 
                    edges_df[dst_col].isin(self.tx_id_to_idx))
            src_idx = edges_df.loc[valid, src_col].map(self.addr_id_to_idx).values
            dst_idx = edges_df.loc[valid, dst_col].map(self.tx_id_to_idx).values
            
        elif edge_type == 'tx-addr':
            # Source is transaction, dest is address
            valid = (edges_df[src_col].isin(self.tx_id_to_idx) & 
                    edges_df[dst_col].isin(self.addr_id_to_idx))
            src_idx = edges_df.loc[valid, src_col].map(self.tx_id_to_idx).values
            dst_idx = edges_df.loc[valid, dst_col].map(self.addr_id_to_idx).values
            
        elif edge_type == 'addr-addr':
            # Both are address IDs
            valid = (edges_df[src_col].isin(self.addr_id_to_idx) & 
                    edges_df[dst_col].isin(self.addr_id_to_idx))
            src_idx = edges_df.loc[valid, src_col].map(self.addr_id_to_idx).values
            dst_idx = edges_df.loc[valid, dst_col].map(self.addr_id_to_idx).values
        
        edge_index = torch.LongTensor(np.vstack([src_idx, dst_idx]))
        
        print(f"   Total edges: {len(edges_df):,}")
        print(f"   Valid edges: {edge_index.shape[1]:,}")
        
        self.stats[f'num_edges_{edge_type}'] = edge_index.shape[1]
        
        return edge_index
    
    def create_temporal_splits(self, timestamps: torch.Tensor, labels: torch.Tensor,
                              train_frac: float = 0.6, val_frac: float = 0.2
                              ) -> Dict[str, torch.Tensor]:
        """
        Create temporal train/val/test splits.
        
        Args:
            timestamps: Node timestamps
            labels: Node labels
            train_frac: Fraction for training
            val_frac: Fraction for validation
        
        Returns:
            Dict with train_mask, val_mask, test_mask
        """
        # Sort timestamps and find boundaries
        sorted_times = np.sort(np.unique(timestamps.numpy()))
        n_timesteps = len(sorted_times)
        
        train_end_idx = int(n_timesteps * train_frac)
        val_end_idx = int(n_timesteps * (train_frac + val_frac))
        
        train_time_end = sorted_times[train_end_idx - 1]
        val_time_end = sorted_times[val_end_idx - 1]
        
        # Create masks (only for labeled nodes)
        labeled = labels >= 0
        train_mask = (timestamps <= train_time_end) & labeled
        val_mask = ((timestamps > train_time_end) & (timestamps <= val_time_end)) & labeled
        test_mask = (timestamps > val_time_end) & labeled
        
        return {
            'train_mask': train_mask,
            'val_mask': val_mask,
            'test_mask': test_mask,
            'train_time_end': int(train_time_end),
            'val_time_end': int(val_time_end)
        }
    
    def build_hetero_data(self, top_k_addresses: Optional[int] = 100000) -> HeteroData:
        """
        Build complete HeteroData object.
        
        Args:
            top_k_addresses: Number of addresses to use (None = all)
        
        Returns:
            HeteroData object
        """
        print("\n" + "="*70)
        print(" BUILDING HETEROGENEOUS GRAPH")
        print("="*70)
        
        # Initialize HeteroData
        data = HeteroData()
        
        # Load transaction nodes
        tx_x, tx_y, tx_timestamps = self.load_transaction_nodes()
        data['transaction'].x = tx_x
        data['transaction'].y = tx_y
        data['transaction'].timestamp = tx_timestamps
        
        # Load address nodes
        addr_x, addr_y, addr_timestamps = self.load_address_nodes(top_k=top_k_addresses)
        data['address'].x = addr_x
        data['address'].y = addr_y
        data['address'].timestamp = addr_timestamps
        
        # Create splits for transactions (primary task)
        splits = self.create_temporal_splits(tx_timestamps, tx_y)
        data['transaction'].train_mask = splits['train_mask']
        data['transaction'].val_mask = splits['val_mask']
        data['transaction'].test_mask = splits['test_mask']
        
        print(f"\n Temporal Splits (Transaction nodes):")
        print(f"   Train: {splits['train_mask'].sum():,} (time  {splits['train_time_end']})")
        print(f"   Val:   {splits['val_mask'].sum():,} (time  {splits['val_time_end']})")
        print(f"   Test:  {splits['test_mask'].sum():,}")
        
        # Load edges
        data['transaction', 'to', 'transaction'].edge_index = self.load_edges('tx-tx')
        data['address', 'to', 'transaction'].edge_index = self.load_edges('addr-tx')
        data['transaction', 'to', 'address'].edge_index = self.load_edges('tx-addr')
        
        # Optional: addr-addr edges (may be very large)
        try:
            data['address', 'to', 'address'].edge_index = self.load_edges('addr-addr')
        except Exception as e:
            print(f"\n Skipping addr-addr edges: {e}")
            self.stats['num_edges_addr-addr'] = 0
        
        # Store metadata
        data.metadata = {
            'node_types': ['transaction', 'address'],
            'edge_types': [
                ('transaction', 'to', 'transaction'),
                ('address', 'to', 'transaction'),
                ('transaction', 'to', 'address'),
                ('address', 'to', 'address')
            ],
            'stats': self.stats
        }
        
        print("\n" + "="*70)
        print(" HETERODATA CONSTRUCTION COMPLETE")
        print("="*70)
        print(f"\nGraph Statistics:")
        print(f"  Nodes:")
        print(f"    Transactions: {data['transaction'].num_nodes:,}")
        print(f"    Addresses: {data['address'].num_nodes:,}")
        print(f"  Edges:")
        for edge_type in data.edge_types:
            src, rel, dst = edge_type
            print(f"    {src}  {dst}: {data[edge_type].num_edges:,}")
        
        return data
    
    def save_hetero_data(self, data: HeteroData, output_dir: Path):
        """Save HeteroData and summary."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Save HeteroData
        torch.save(data, output_dir / 'hetero_graph.pt')
        print(f"\n Saved HeteroData: {output_dir / 'hetero_graph.pt'}")
        
        # Save summary
        summary = {
            'num_nodes': {
                'transaction': data['transaction'].num_nodes,
                'address': data['address'].num_nodes
            },
            'num_edges': {
                f"{src}_to_{dst}": data[edge_type].num_edges
                for src, rel, dst in data.edge_types
                for edge_type in [(src, rel, dst)]
            },
            'num_labeled': {
                'transaction': (data['transaction'].y >= 0).sum().item(),
                'address': (data['address'].y >= 0).sum().item()
            },
            'temporal_range': {
                'transaction': [
                    data['transaction'].timestamp.min().item(),
                    data['transaction'].timestamp.max().item()
                ],
                'address': [
                    data['address'].timestamp.min().item(),
                    data['address'].timestamp.max().item()
                ]
            },
            'feature_dims': {
                'transaction': data['transaction'].x.shape[1],
                'address': data['address'].x.shape[1]
            },
            'splits': {
                'train': data['transaction'].train_mask.sum().item(),
                'val': data['transaction'].val_mask.sum().item(),
                'test': data['transaction'].test_mask.sum().item()
            }
        }
        
        with open(output_dir / 'hetero_graph_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print(f" Saved summary: {output_dir / 'hetero_graph_summary.json'}")
        
        # Save node mappings
        mappings = {
            'tx_id_to_idx': {str(k): int(v) for k, v in self.tx_id_to_idx.items()},
            'addr_id_to_idx': {str(k): int(v) for k, v in self.addr_id_to_idx.items()}
        }
        with open(output_dir / 'node_mappings.json', 'w') as f:
            json.dump(mappings, f, indent=2)
        print(f" Saved mappings: {output_dir / 'node_mappings.json'}")


def main():
    """Build heterogeneous graph from Elliptic++ data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build Heterogeneous Graph')
    parser.add_argument('--data_root', type=str, default='data/Elliptic++ Dataset',
                       help='Path to data directory')
    parser.add_argument('--output_dir', type=str, default='data',
                       help='Output directory')
    parser.add_argument('--top_k_addresses', type=int, default=100000,
                       help='Number of addresses to use (None for all)')
    parser.add_argument('--all_addresses', action='store_true',
                       help='Use all addresses instead of top K')
    
    args = parser.parse_args()
    
    # Build graph
    builder = HeteroGraphBuilder(
        data_root=args.data_root,
        use_all_addresses=args.all_addresses
    )
    
    top_k = None if args.all_addresses else args.top_k_addresses
    data = builder.build_hetero_data(top_k_addresses=top_k)
    
    # Save
    builder.save_hetero_data(data, output_dir=args.output_dir)
    
    print("\n E5 Milestone Complete!")


if __name__ == '__main__':
    main()
