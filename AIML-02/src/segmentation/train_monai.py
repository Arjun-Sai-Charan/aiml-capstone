"""Train the educational 3D U-Net on MSD Hippocampus or synthetic demo volumes."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch


def foreground_dice(prediction: torch.Tensor, target: torch.Tensor) -> tuple[float | None, dict[str, float]]:
    """Return mean Dice over foreground labels 1 and 2, excluding absent labels."""
    scores: dict[str, float] = {}
    for label in (1, 2):
        pred_mask = prediction == label
        target_mask = target == label
        denom = int(pred_mask.sum().item() + target_mask.sum().item())
        if denom:
            scores[str(label)] = float(2 * (pred_mask & target_mask).sum().item() / denom)
    return (float(np.mean(list(scores.values()))) if scores else None), scores


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Use synthetic volumes if MSD is unavailable')
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--msd', help='Path to Task04_Hippocampus; otherwise use MSD_DIR')
    parser.add_argument('--output', default='AIML-02/outputs/segmentation')
    args = parser.parse_args()

    base = Path(args.msd or os.getenv('MSD_DIR', 'AIML-02/data/raw/msd/Task04_Hippocampus'))
    images = base / 'imagesTr'
    labels = base / 'labelsTr'
    listing = base / 'dataset.json'
    demo = not (images.is_dir() and labels.is_dir() and listing.is_file())
    if demo and not args.demo:
        raise FileNotFoundError(
            f'MSD Hippocampus dataset not found at {base}; set MSD_DIR or run '
            'python run.py train-seg -- --demo'
        )
    if args.epochs < 1:
        parser.error('--epochs must be at least 1')

    from monai.data import DataLoader, Dataset
    from monai.inferers import sliding_window_inference
    from monai.losses import DiceLoss
    from monai.networks.nets import UNet
    from monai.transforms import Compose, EnsureChannelFirstd, EnsureTyped, LoadImaged, ScaleIntensityd

    if demo:
        rng = np.random.default_rng(9)
        data = []
        for _ in range(4):
            image = rng.random((1, 32, 32, 32), dtype=np.float32)
            target = np.zeros((1, 32, 32, 32), dtype=np.int16)
            target[:, 7:15, 9:17, 10:18] = 1
            target[:, 18:26, 16:24, 17:25] = 2
            data.append({'image': image, 'label': target})
    else:
        from monai.data import load_decathlon_datalist
        files = load_decathlon_datalist(str(listing), True, 'training')
        transform = Compose([
            LoadImaged(keys=['image', 'label']),
            EnsureChannelFirstd(keys=['image', 'label']),
            ScaleIntensityd(keys='image'),
            EnsureTyped(keys=['image', 'label']),
        ])
        data = Dataset(files, transform)

    loader = DataLoader(data, batch_size=1, shuffle=True)
    # MSD Task04_Hippocampus labels are background (0) and two hippocampal regions (1, 2).
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = UNet(
        spatial_dims=3, in_channels=1, out_channels=3,
        channels=(8, 16, 32, 64), strides=(2, 2, 2), num_res_units=1,
    ).to(device)
    loss_fn = DiceLoss(to_onehot_y=True, softmax=True, include_background=False)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(args.epochs):
        model.train()
        losses = []
        for batch in loader:
            image = batch['image'].to(device).float()
            target = batch['label'].to(device).long()
            optimizer.zero_grad()
            loss = loss_fn(model(image), target)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))
        print(f'epoch {epoch + 1}: dice_loss={float(np.mean(losses)):.6f}')

    # This is an illustrative training-batch score; no held-out MSD split is claimed.
    model.eval()
    batch = next(iter(loader))
    image = batch['image'].to(device).float()
    target = batch['label'].to(device).long().squeeze(1)
    with torch.no_grad():
        logits = sliding_window_inference(image, (32, 32, 32), 1, model)
        prediction = logits.argmax(dim=1)
    dice, per_label = foreground_dice(prediction, target)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output / 'unet.pt')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    slice_index = image.shape[-1] // 2
    fig, ax = plt.subplots()
    ax.imshow(image[0, 0, :, :, slice_index].detach().cpu().numpy(), cmap='gray')
    shown = prediction[0, :, :, slice_index].detach().cpu().numpy()
    ax.imshow(np.ma.masked_where(shown == 0, shown), alpha=0.45, cmap='autumn', vmin=0, vmax=2)
    ax.set_title('Predicted hippocampus regions (training sample)')
    fig.savefig(output / 'slice_overlay.png', bbox_inches='tight')
    plt.close(fig)

    metrics = {
        'demo': demo,
        'epochs': args.epochs,
        'device': str(device),
        'dice_score': dice,
        'dice_per_label': per_label,
        'score_split': 'training batch (illustrative, not held-out)',
    }
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    print(metrics)


if __name__ == '__main__':
    main()
