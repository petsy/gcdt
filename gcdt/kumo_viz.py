#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Visualize cloudformation template."""

from __future__ import print_function
import sys
from numbers import Number
from compiler.ast import flatten

# based on original version from https://github.com/benbc/cloud-formation-viz
# Author: Ben Butler-Cole
# License: MIT

# sample use:
# with open('ELBStickinessSample.template', 'r') as tfile:
#    template = json.loads(tfile.read())
# cfn_viz(template, parameters={'KeyName': 'abc123'})


def cfn_viz(template, parameters=[], outputs=[], out=sys.stdout):
    """Render dot output for cloudformation.template in json format.
    """
    (graph, edges) = extract_graph(template.get('Description', ''),
                                   template['Resources'])
    graph['edges'].extend(edges)
    handle_terminals(template, graph, 'Parameters', 'source', parameters)
    handle_terminals(template, graph, 'Outputs', 'sink', outputs)
    graph['subgraphs'].append(handle_psuedo_params(graph['edges']))

    render(graph, out=out)


def handle_terminals(template, graph, name, rank, values={}):
    if name in template:
        (subgraph, edges) = extract_graph_terminals(name, template[name], values)
        subgraph['rank'] = rank
        subgraph['style'] = 'filled,rounded'
        graph['subgraphs'].append(subgraph)
        graph['edges'].extend(edges)


def handle_psuedo_params(edges):
    graph = {
        'name': 'Psuedo Parameters', 'nodes': [], 'edges': [],
        'subgraphs': []
    }
    graph['shape'] = 'ellipse'
    params = set()
    for e in edges:
        if e['from'].startswith(u'AWS::'):
            params.add(e['from'])
    graph['nodes'].extend({'name': n} for n in params)
    return graph


def get_fillcolor(resource_type, properties):
    """Determine fillcolor for resources (public ones in this case)
    """
    fillcolor = None
    # LoadBalancer
    if resource_type == 'LoadBalancer':
        if ('Scheme' not in properties) or \
                properties['Scheme'] == 'internet-facing':
            fillcolor = 'red'

    return fillcolor


def extract_graph(name, elem):
    graph = {'name': name, 'nodes': [], 'edges': [], 'subgraphs': []}
    edges = []
    for item, details in elem.iteritems():
        # item: ElasticLoadBalancer
        # details: {u'Type': u'AWS::ElasticLoadBalancing::LoadBalancer', u'Properties': {u'Scheme': u'internet-facing',...
        node = {'name': item}
        if 'Type' in details:
            resource_type = details['Type'].split('::')[-1]
            if resource_type:
                node['type'] = resource_type
                if 'Properties' in details:
                    fillcolor = get_fillcolor(resource_type,
                                              details['Properties'])
                    if fillcolor:
                        node['fillcolor'] = fillcolor
        graph['nodes'].append(node)
        # edges.extend(flatten(find_refs(item, details)))
        edges.extend(flatten(find_refs(item, details)))
    return graph, edges


def extract_graph_terminals(name, elem, values={}):
    graph = {'name': name, 'nodes': [], 'edges': [], 'subgraphs': []}
    edges = []
    for item, details in elem.iteritems():
        node = {'name': item}
        if item in values:
            node['value'] = values[item]
        graph['nodes'].append(node)
        edges.extend(flatten(find_refs(item, details)))
    return graph, edges


def find_refs(context, elem):
    if isinstance(elem, dict):
        refs = []
        for k, v in elem.iteritems():
            if unicode(k) == unicode('Ref'):
                assert isinstance(v, basestring), 'Expected a string: %s' % v
                refs.append({'from': v, 'to': context})
            elif unicode(k) == unicode('Fn::GetAtt'):
                assert isinstance(v, list), 'Expected a list: %s' % v
                refs.append({'from': v[0], 'to': context})
            else:
                refs.extend(find_refs(context, v))
        return refs
    elif isinstance(elem, list):
        return map(lambda e: find_refs(context, e), elem)
    elif isinstance(elem, basestring):
        return []
    elif isinstance(elem, bool):
        return []
    elif isinstance(elem, Number):
        return []
    else:
        raise AssertionError('Unexpected type: %s' % elem)


def render(graph, subgraph=False, out=sys.stdout):
    def _render_node(n):
        # helper to render a node (this adds type and fillcolor)
        # styles here: http://www.graphviz.org/doc/info/attrs.html#d:fillcolor
        if 'fillcolor' in n:
            # fillcolor ON
            print('node [style="filled"];', file=out)
            print('node [fillcolor="%s"]' % n['fillcolor'], file=out)
        if 'value' in n:
            # use HTML labels:
            # http://stackoverflow.com/questions/19280229/graphviz-putting-a-caption-on-a-node-in-addition-to-a-label
            print('"%s"[label=<%s<BR /><FONT POINT-SIZE="8">[=%s]</FONT>>]' %
                  (n['name'], n['name'], n['value']), file=out)
        elif 'type' in n:
            print('"%s"[label=<<FONT POINT-SIZE="8">[%s]</FONT><BR />%s>]' %
                  (n['name'], n['type'], n['name']), file=out)
        else:
            print('"%s"' % n['name'], file=out)
        if 'fillcolor' in n:
            # fillcolor OFF
            print('node [style=""];', file=out)
            print('node [fillcolor=""]', file=out)

    if subgraph:
        print('subgraph "%s" {' % graph['name'], file=out)
    else:
        print('digraph "%s" {' % graph['name'], file=out)
    print('labeljust=l;', file=out)
    print('node [shape={}];'.format(graph.get('shape', 'box')), file=out)
    if 'style' in graph:
        print('node [style="%s"]' % graph['style'], file=out)
    if 'rank' in graph:
        print('rank=%s' % graph['rank'], file=out)
    for node in graph['nodes']:
        _render_node(node)
    for s in graph['subgraphs']:
        render(s, True, out)
    for e in graph['edges']:
        print('"%s" -> "%s";' % (e['from'], e['to']), file=out)
    print('}', file=out)
