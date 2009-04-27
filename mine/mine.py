"""
A my wiki kind of thing.
"""

import logging
import urllib

from jinja2 import Environment, FileSystemLoader

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import UserRequiredError, ForbiddenError
from tiddlyweb.web.http import HTTP400, HTTP302
from tiddlywebplugins import do_html, entitle, require_any_user


template_env = Environment(loader=FileSystemLoader('templates'))

@do_html()
@entitle('Mine!')
def mine(environ, start_response):
    logout_link = '%s/logout' % (environ['tiddlyweb.config']['server_prefix'])
    login_link = '%s/challenge/openid?tiddlyweb_redirect=%s' % (
            environ['tiddlyweb.config']['server_prefix'],
            urllib.quote(environ['tiddlyweb.config']['server_prefix'] + '/mine', safe=''))
    recipes = _readable_recipes(environ)
    myrecipes = []
    bags = []
    if environ['tiddlyweb.usersign']['name'] == 'GUEST':
        template_name = 'all.html'
        message = """
Create and manage <a href='http://tiddlyweb.peermore.com/wiki/#TiddlyWebWiki'>TiddlyWebWikis</a>.
"""
    else:
        template_name = 'mine.html'
        myrecipes = _my_recipes(environ, recipes)
        bags = _readable_bags(environ)
        message = ''
    template = template_env.get_template(template_name)
    return template.generate(
            login_link=login_link,
            logout_link=logout_link,
            recipes=recipes,
            myrecipes=myrecipes,
            bags=bags,
            message=message)


@require_any_user()
def manage_mine(environ, start_response):
    """Handle POST"""
    # put a try around this stuff eventually
    creation = environ['tiddlyweb.query']['creatego'][0]
    if creation == 'Quick!':
        _quick_create(environ)
    elif creation == 'Create Recipe':
        _create_recipe(environ)
    elif creation == 'Create Bag':
        _create_bag(environ)
    else:
        raise HTTP400('Improper Form Submit')
    home_uri = '%s/mine' % environ['tiddlyweb.config']['server_prefix']
    raise HTTP302(home_uri)

def _quick_create(environ):
    pass

def _create_recipe(environ):
    pass

def _create_bag(environ):
    """Take the form input and turn it into a bag."""
    query_data = _flatten_form_data(environ['tiddlyweb.query'])
    logging.debug(query_data)
    try:
        new_bag = Bag(query_data['bag_name'])

        if _bag_exists(new_bag):
            raise HTTP409('That bag may not be created.')

        username = environ['tiddlyweb.usersign']['name']
        new_bag.policy.owner = username
        new_bag.policy.manage = [username]
        new_bag.desc = query_data['bag_desc']

        for policy_type in ('read', 'write', 'create', 'delete'):
            texted = query_data.get(policy_type + '_text', None)
            logging.debug('texted: %s' % texted)
            if texted:
                new_bag.policy.__setattr__(policy_type, [x.lstrip().rstrip() for x in texted.split(',')])
            else:
                set = query_data[policy_type]
                new_bag.policy.__setattr__(policy_type, _policy_form_to_entry(username, set))

        store = environ['tiddlyweb.store']
        store.put(new_bag)
    except KeyError, exc:
        raise HTTP400('something went wrong processing for: %s' % exc)
    return True


def _policy_form_to_entry(username, set_name):
    if set_name == 'private':
        return [username]
    if set_name == 'any':
        return ['ANY']
    if set_name == 'public':
        return []


def _bag_exists(bag):
    return False


def _flatten_form_data(form_dict):
    """We assume we only want the first value in any listed data."""
    query_data = {}
    for key, value in form_dict.items():
        query_data[key] = value[0]
    return query_data


def init(config):
    config['selector'].add('/mine', GET=mine, POST=manage_mine)


def _readable_bags(environ):
    store = environ['tiddlyweb.store']
    bags = store.list_bags()
    kept_bags = []
    for bag in bags:
        try:
            bag = store.get(bag)
            bag.policy.allows(environ['tiddlyweb.usersign'], 'read')
            kept_bags.append(bag)
        except(UserRequiredError, ForbiddenError):
            pass
    return kept_bags


def _readable_recipes(environ):
    store = environ['tiddlyweb.store']
    recipes = store.list_recipes()
    kept_recipes = []
    for recipe in recipes:
        try:
            recipe = store.get(recipe)
            recipe.policy.allows(environ['tiddlyweb.usersign'], 'read')
            kept_recipes.append(recipe)
        except(UserRequiredError, ForbiddenError):
            pass
    return kept_recipes


def _my_recipes(environ, recipes):
    user = environ['tiddlyweb.usersign']['name']
    kept_recipes = []
    for recipe in recipes:
        if recipe.policy.owner == user:
            kept_recipes.append(recipe)
    return kept_recipes
