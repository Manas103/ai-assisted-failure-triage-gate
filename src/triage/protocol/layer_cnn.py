"""A compact character-level 1D-CNN that attributes a protocol log line to
the stack layer responsible (PHY, MAC, RLC, RRC, NAS). Character-level
because these log lines are not natural-language prose (identifiers, hex
addresses, numeric fields dominate), which is also the published reason a
compact classifier beats an LLM on this data shape (see README sources)."""
import numpy as np
import torch
import torch.nn as nn

from triage.protocol.generate_protocol_logs import LAYERS

MAX_LEN = 160
VOCAB_SIZE = 128  # ASCII


def encode(messages, max_len=MAX_LEN):
    arr = np.zeros((len(messages), max_len), dtype=np.int64)
    for i, m in enumerate(messages):
        b = m.encode("ascii", errors="replace")[:max_len]
        arr[i, :len(b)] = list(b)
    return arr


class LayerCNN(nn.Module):
    def __init__(self, n_classes=len(LAYERS), vocab_size=VOCAB_SIZE, emb_dim=16, channels=32):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim)
        self.conv1 = nn.Conv1d(emb_dim, channels, kernel_size=5, padding=2)
        self.conv2 = nn.Conv1d(channels, channels, kernel_size=5, padding=2)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc = nn.Linear(channels, n_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        h = self.emb(x).transpose(1, 2)  # [B, emb_dim, L]
        h = self.relu(self.conv1(h))
        h = self.relu(self.conv2(h))
        h = self.pool(h).squeeze(-1)
        return self.fc(h)


def train_and_eval(records, epochs=8, seed=0, test_frac=0.2):
    from sklearn.metrics import f1_score

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    label_idx = {l: i for i, l in enumerate(LAYERS)}

    messages = [r["message"] for r in records]
    labels = np.array([label_idx[r["layer"]] for r in records], dtype=np.int64)
    X = encode(messages)

    n = len(labels)
    perm = rng.permutation(n)
    n_test = int(n * test_frac)
    test_idx, train_idx = perm[:n_test], perm[n_test:]

    Xtr, ytr = torch.from_numpy(X[train_idx]), torch.from_numpy(labels[train_idx])
    Xte, yte = torch.from_numpy(X[test_idx]), torch.from_numpy(labels[test_idx])

    model = LayerCNN()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    batch = 256
    n_train = len(ytr)
    for epoch in range(epochs):
        model.train()
        order = torch.randperm(n_train)
        tot_loss = 0.0
        for i in range(0, n_train, batch):
            idx = order[i:i + batch]
            opt.zero_grad()
            logits = model(Xtr[idx])
            loss = loss_fn(logits, ytr[idx])
            loss.backward()
            opt.step()
            tot_loss += loss.item() * len(idx)

    model.eval()
    with torch.no_grad():
        pred_te = model(Xte).argmax(dim=-1).numpy()
    macro_f1 = f1_score(yte.numpy(), pred_te, average="macro")

    return dict(model=model, macro_f1=float(macro_f1), n_train=n_train, n_test=len(yte),
                test_idx=test_idx, pred_test=pred_te, y_test=yte.numpy())
