local lib = import 'infotab_train.libsonnet';


local verification_train = lib.trainer("verification", "data/totto2/triplets/", 1e-6);

{
    steps: verification_train
}