# Databricks notebook source
# SYNTHETIC example notebook.
from lakehouse.transforms import silver_orders


def run(rows):
    return silver_orders(rows)
