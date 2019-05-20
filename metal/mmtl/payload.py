import torch
from metal.mmtl.data import MmtlDataLoader, MmtlDataset

class Payload(object):
    """A bundle of data_loaders...

    Args:
        name: the name of the payload (i.e., the name of the instance set)
        data_loaders: A dict of DataLoaders to feed through the network
            Each key in data.keys() should be in ["train", "valid", "test"]
            The DataLoaders should return batches of (X, Ys) pairs, where X[0] returns
                a complete input for feeding into the input_module, and Ys is a dict of
                the form {task_name: Y} and Y is an [n, ?] tensor
        labels_to_tasks
    """

    def __init__(self, name, data_loader, labels_to_tasks, split):
        self.name = name
        self.data_loader = data_loader
        self.labels_to_tasks = labels_to_tasks
        self.split = split

    def __repr__(self):
        return (
            f"Payload({self.name}: labels_to_tasks=[{self.labels_to_tasks}], "
            f"split={self.split})"
        )

    @classmethod
    def from_tensors(self, name, X, Y, task_name, split, **data_loader_kwargs):
        """A shortcut for creating a Payload for data with one field and one label set
        name: the name of this Payload
        X: a Tensor of data of shape [n, ?]
        Y: a Tensor of labels of shape [n, ?]
        task_name: the name of the Task that the label set Y corresponds to
        split: the string name of the split that this Payload corresponds to
        X and Y will be packaged into an MmtlDataset that will be wrapped in an
        MmtlDataLoader.
        """
        dataset = MmtlDataset(X, Y)
        data_loader = MmtlDataLoader(dataset, **data_loader_kwargs)
        labels_to_tasks = {"labels": task_name}
        return Payload(name, data_loader, labels_to_tasks, split)
    
    def add_label_set(
        self, task_name, label_name, label_list=None, label_fn=None, verbose=True
    ):
        """Adds a new label_set to an existing payload

        Args:
            task_name: the name of the Task to which the label_set belongs
            label_name: the name of the label_set being added
            label_fn: a function which maps a dataset item to a label
                labels will be combined using torch.stack(labels, dim=0)
            label_list: a list of labels in the correct order

        Note that either label_fn or label_list should be provided, but not both.
        """

        if label_fn is not None:
            assert label_list is None
            assert callable(label_fn)
            new_labels = torch.stack(
                [label_fn(x) for x in self.data_loader.dataset], dim=0
            )
        elif label_list is not None:
            assert label_fn is None
            assert isinstance(label_list, torch.Tensor)
            new_labels = label_list
        else:
            raise ValueError("Incorrect label object type -- supply list or function")

        if new_labels.dim() < 2:
            raise Exception("New label_set must have at least two dimensions: [n, ?]")

        self.data_loader.dataset.labels[task_name] = new_labels
        self.labels_to_tasks[label_name] = task_name

        if verbose:
            active = torch.any(new_labels != 0, dim=1)
            msg = (
                f"Added label_set with {sum(active.long())}/{len(active)} labels for "
                f"task {task_name} to payload {self.name}."
            )
            print(msg)

    def remove_label_set(self, label_name, verbose=True):
        self.data_loader.dataset.labels.pop(label_name)
        task_name = self.labels_to_tasks[label_name]
        del self.labels_to_tasks[label_name]

        if verbose:
            print(
                f"Removed label_set {label_name} for task {task_name} from payload {self.name}."
            )

    def _retarget_labelset(self, label_name, task_name, verbose=True):
        """Retargets a labelset to the specified task name (in labels_to_tasks). """

        old_task = self.labels_to_tasks[label_name]
        if old_task != task_name:
            self.labels_to_tasks[label_name] = task_name
            if verbose:
                print(
                    f"labelset '{label_name}' -> task '{self.labels_to_tasks[label_name]}' "
                    f"(originally, {old_task})."
                )

    def remap_labelsets(self, labels_to_tasks, default_none=False, verbose=True):
        """ Remaps payload.labels_to_tasks based on specified dictionary. All other
            defaults to `labelset` -> `None`.

        Args:
            labels_to_heads: if specified, remaps (in-place) labelsets to specified
                task heads.

        """
        test_labelsets = self.labels_to_tasks.keys()
        for label_name in test_labelsets:
            if label_name in labels_to_tasks:
                new_task = labels_to_tasks[label_name]
                self._retarget_labelset(label_name, new_task, verbose=verbose)
            else:
                if default_none:
                    self._retarget_labelset(label_name, None, verbose=verbose)
