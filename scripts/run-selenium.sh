#!/bin/bash
#Los siguientes modules los ignoramos porque tienen tests vacios: fakenodo webhook featuremodel flamapy hubfile
#EL reset de la BD y El orden es importante porque hay algun test que modifica BD 
rosemary db:reset -y && rosemary db:seed && rosemary selenium auth && rosemary selenium explore && pytest app/modules/dataset/tests/test_selenium3.py && rosemary selenium dataset && pytest app/modules/dataset/tests/test_selenium2.py