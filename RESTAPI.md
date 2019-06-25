## Contents

#### Misc useful stuff
* [Data types](#data-types)
* [Graph-specific endpoint query parameters](#graph-specific-endpoint-query-parameters)
* [Bulk endpoint query parameters](#bulk-endpoint-query-parameters)
* [Magic meta keys](#magic-meta-keys)

#### Graph query and manipulation
* [/graph](#graph)
* [/graph/{*uuid*}](#graphuuid)
* [/graph/{*uuid*}/meta](#graphuuidmeta)
* [/graph/{*uuid*}/seeds](#graphuuidseeds)
* [/graph/{*uuid*}/status](#graphuuidstatus)
* [/graph/{*uuid*}/node/{*ID*}](#graphuuidnodeid)
* [/graph/{*uuid*}/edge/{*ID*}](#graphuuidedgeid)
* [/reset/{*uuid*}](#resetuuid)

#### Server-side execution
* [/graph/exec](#graphexec)
* [/graph/{*uuid*}/exec](#graphuuidexec)

#### Non-logged per-graph key/value store
* [/kv/{*uuid*}](#kvuuid)
* [/kv/{*uuid*}/{*key*}](#kvuuidkey)

#### Presentation
* [/view/{*uuid*}](#viewuuid)
* [/d3/{*uuid*}](#d3uuid)

#### LG-Lite API
* [/lg](#lg)
* [/lg/config/{*job_uuid*}](#lgconfigjob_uuid)
* [/lg/config/{*job_uuid*}/{*adapter*}](#lgconfigjob_uuidadapter)
* [/lg/adapter/{*adapter*}](#lgadapteradapter)
* [/lg/adapter/{*adapter*}/{*job_uuid*}](#lgadapteradapterjob_uuid)
* [/lg/adapter/{*adapter*}/{*job_uuid*}/{*task_uuid*}](#lgadapteradapterjob_uuidtask_uuid)

---

#### Data Types
* *uint* - unsigned integer
* *uuid* - time-based v1 uuids
* *flag* - true if present and not set to '0', 'false', or 'no', else false
* *pattern* - [LemonGraph query language pattern](README.md#query-language)
* *date/time* - date/time string that python's dateutil can parse:
	* `2019-06-11T15:12:19.759817Z`
	* `2019-06-11T11:12:19.759817-0400`
	* `2019-06-11 11:12:19.759817 EST`
* *boolean* - standard boolean
* *string* - standard string
* *dict* - standard dict/object/hashmap
* *list* - standard list/array

#### Graph-specific endpoint query parameters
All graph-specific endpoints (any with *uuid*) include the following query parameters:
* __user__ (*string*):
	* ensures supplied user is valid for graph
	* __role__ (*string*):
		* multiple may be specified
		* ensures user has at least one of the supplied roles for graph

#### Bulk endpoint query parameters
Bulk endpoints (__GET__ [/graph](#graph), __POST__ [/graph/exec](#graphexec)) include the following query parameters:
* __user__ (*string*):
	* restrict graphs to those having specified user
	* __role__ (*string*):
		* multiple may be specified
		* restrict to graphs with user having at least one of the supplied roles
* __created_after__ (*date/time*):
	* restrict graphs to those created after supplied date/time
* __created_before__ (*date/time*):
	* restrict graphs to those created before supplied date/time
* __enabled__ (*flag*):
	* restrict graphs to those marked as enabled
* __filter__ (*string*):
	* multiple may be specified
	* applies LG node/edge [query language](README.md#query-language)-ish string[s] to graph meta
		* leave off the leading `e(` or `n(` and trailing `)`

#### Magic meta keys
If present, several meta keys are harvested, transformed, and cached in the global graph index:
* __enabled__ (*boolean*):
	* default: __true__
	* can be used to [filter bulk endpoints](#bulk-endpoint-query-parameters)
	* used by [LG-Lite](#jobs)
* __priority__ (*uint*):
	* clamped to be in numeric range [0-255], default: 100
	* used by [LG-Lite](#jobs)
* __roles__ (*dict*):
	* non-dicts are ignored
	* keys are users
	* values can be either:
		* strings of one or more whitespace-separated roles
		* objects containing key/value pairs:
			* __role__: *boolean*
	* For example:
		```json
		{
			"alice" : "reader writer",
			"bob": { "reader": true, "writer": false }
		}
		```

---

#### /graph
* __GET__ - Bulk retrieve graph meta, or bulk graph query
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role/created_after/created_before/enabled/filter__](#bulk-endpoint-query-parameters)
		* __q__: *pattern*, multiple may be specified
			* executes queries against multiple graphs
	* Uses most of the above query parameters to determine target graphs.
	* If graph queries are supplied (via the __q__ query parameter), execute queries against graphs. Returned format will be list of lists, such that:
		* first entry is the supplied list of query patterns
		* subsequent entries are tuples of: graph id, query index, and chain
	* Else, returns list of graphs, including graph meta and a few other magic fields.
* __POST__ - Create a new graph
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
		* Content-Type: `application/json`, `application/x-msgpack`
	* Optionally supplied body should be object containing zero or more of the following key/value pairs:
		* __seed__ (*boolean*): mark any supplied nodes/edges as seeds. Seed nodes will be assigned __depth__ = 0
		* __meta__ (*dict*): top level graph metadata key/value pairs to merge in
		* __chains__ (*list*): list of node[->edge->node]\* chains
		* __nodes__ (*list*): list of node objects
		* __edges__ (*list*): list of edge objects
		* __adapters__ (*list*): list of [LG-Lite adapter objects](#lgconfigjob_uuidadapter)
	* node objects must include primary key data:
		* __type__ (*string*)
		* __value__ (*string*)
	* for edge objects, __value__ (*string*) is optional and defaults to the empty string
	* edge objects referenced in __chains__ must include:
		* __type__ (*string*)
	* edge objects referenced in __edges__ must include:
		* __type__ (*string*)
		* __src__ (*node*)
		* __tgt__ (*node*)
	* Nodes and edges will be created if nodes with __type__/__value__ or edges with __type__/__value__/__src__/__tgt__ do not already exist.
	* Any supplied __ID__ fields are ignored.
	* Any supplied __depth__ property on a node is silently ignored (use __seed__ flag to set node __depth__ = 0). Non-seed-node depths are calculated.
	* Any supplied __cost__ property on an edge is silently ignored if either is true:
		* __cost__ < 0 or __cost__ > 1
		* __cost__ > target edge's current cost
	* Any otherwise reserved attributes will be ignored.
	* Any other supplied node/edge attributes will be merged in.
	* Returns object containing: __id__: *uuid*

#### /graph/{*uuid*}
* __HEAD__ - Check graph existance, pull headers
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __GET__ - Pull full graph contents or execute queries
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`, `application/octet-stream`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
		* __q__ (*pattern*):
			* executes supplied query patterns against target graph
			* __crawl__ (*flag*):
				* use generated chains as starting points to crawl and return the accessible sub-graph
			* __start__ (*uint*):
				* execute in streaming mode starting at supplied log position
			* __stop__ (*uint*):
				* if __start__ is also supplied, end the streaming query immediately after this log position
				* else execute the query as of this log position
			* __limit__ (*uint*):
				* stop after generating this many chains
	* query parameters are ignored for `application/octet-stream` output - a binary graph snapshot is returned
	* requests returning [sub]graphs require `application/json` output - either no query patterns, or query patterns with __crawl__ set
	* requests returning chains may use `application/json` or `application/x-msgpack`
	* chains are returned as a sequence of lists
		* first entry is a sorted list of the requested query patterns
		* remaining entries are tuples of query pattern index and matching chain
* __POST__ - Merge data into existing graph
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
		* __create__ (*flag*): if set, create graph if it doesn't exist. Use v1 (time-based) uuids only.
	* Optionally supplied body should be object containing zero or more of the following key/value pairs:
		* __seed__ (*boolean*): mark any supplied nodes/edges as seeds. Seed nodes will be assigned __depth__ = 0
		* __meta__ (*dict*): top level graph metadata key/value pairs to merge in
		* __chains__ (*list*): list of node[->edge->node]\* chains
		* __nodes__ (*list*): list of node objects
		* __edges__ (*list*): list of edge objects
		* __adapters__ (*list*): list of [LG-Lite adapter objects](#lgconfigjob_uuidadapter)
	* node objects must include primary key data:
		* either:
			* __type__ (*string*)
			* __value__ (*string*)
		* or:
			* __ID__ (*uint*)
	* for edge objects, __value__ (*string*) is optional and defaults to the empty string
	* edge objects referenced in __chains__ must include:
		* either:
			* __type__ (*string*)
		* or:
		  * __ID__ (*uint*)
	* edge objects referenced in __edges__ must include:
		* either:
			* __type__ (*string*)
			* __src__ (*node*)
			* __tgt__ (*node*)
		* or:
			* __ID__ (*uint*)
	* Nodes and edges will be created if nodes with __type__/__value__ or edges with __type__/__value__/__src__/__tgt__ do not already exist.
	* If creating a new graph, any supplied __ID__ fields are ignored.
	* Any supplied __depth__ property on a node is silently ignored (use __seed__ flag to set node __depth__ = 0). Non-seed-node depths are calculated.
	* Any supplied __cost__ property on an edge is silently ignored if either is true:
		* __cost__ < 0 or __cost__ > 1
		* __cost__ > target edge's current cost
	* Any otherwise reserved attributes will be ignored.
	* Any other supplied node/edge attributes will be merged in.
* __PUT__ - Upload binary graph
	* Request headers:
		* Accept: `application/octet-stream`
	* expects graph binary data as input
* __DELETE__ - Delete graph
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

#### /graph/{*uuid*}/meta
* __GET__ - Pull graph metadata
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __PUT__ - Merge in graph metadata
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

#### /graph/{*uuid*}/seeds
* __GET__ - Pull ordered list of posted payloads that were marked as seeds.
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

#### /graph/{*uuid*}/status
* __GET__ - Query central index for graph metadata, size, node/edge count, create date
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __HEAD__ - Same as __GET__, but return no data
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

#### /graph/{*uuid*}/node/{*ID*}
* __GET__ - Pull graph node by __ID__
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __PUT__ - Update graph node by __ID__
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
	* Body should be an object with key/value pairs to merge.

#### /graph/{*uuid*}/edge/{*ID*}
* __GET__ - Pull graph edge by __ID__
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __PUT__ - Update graph edge by __ID__
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
	* Body should be an object with key/value pairs to merge.

#### /reset/{*uuid*}
* __PUT__ - Clear graph and re-insert the first POST marked as seed data, if present.
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
	* Payload should be empty. __FIXME__ - this not *entirely* accurate.

---

#### /graph/exec
* __POST__ - Bulk execute handler against multiple graphs
	* Request headers:
		* Accept: `application/python`
	* Query parameters:
		* [__user/role/created_after/created_before/enabled/filter__](#bulk-endpoint-query-parameters)
	* Request body should be python that at minimum defines a handler function
		* After loading, it will be called with:
			* a generator that yields tuples of read-only transaction handle and matching uuid
			* the response headers object
			* and any supplied QUERY_STRING parameters as named parameters, excluding above query parameters
	* Example handler function:
		```python
		def handler(txns_uuids, headers, **kwargs):
			pass
		```

#### /graph/{*uuid*}/exec
* __POST__ - Execute handler against graph
	* Request headers:
		* Accept: `application/python`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
	* Request body should be python that at minimum defines a handler function
		* After loading, it will be called with:
			* a read-only transaction handle
			* the graph uuid
			* the response headers object
			* any supplied QUERY_STRING parameters as named parameters, excluding above query parameters
	* Example handler function:
		```python
			def handler(txn, uuid, headers, **kwargs):
				pass
		```

---

#### /kv/{*uuid*}
* __GET__ - Retrieve dictionary
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __PUT__ - Overwrite dictionary
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __POST__ - Merge dictionary
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __DELETE__ - Delete dictionary
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

#### /kv/{*uuid*}/{*key*}
* __GET__ - Retrive value for specific dictionary key
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __PUT__ - Overwrite specific dictionary key value
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __POST__ - Merge specific dictionary key value
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)
* __DELETE__ - Delete specific dictionary key
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

---

#### /view/{*uuid*}
* __GET__ - Return basic view of graph as a D3 force graph
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

#### /d3/{*uuid*}
* __GET__ - Stream D3-friendly json dump of graph
	* Query parameters:
		* [__user/role__](#graph-specific-endpoint-query-parameters)

---

#### /lg
* __GET__ - Return number of jobs that might have work, per query per adapter
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`

#### /lg/config/{*job_uuid*}
* __GET__ - Return _job\_uuid_'s config/status per query per adapter
	* Request headers:
		* Accept: `application/json`, `application/x-msgpack`
* __POST__ - Update one or more adapter configs
	* Request headers:
		* Content-Type: `application/json`, `application/x-msgpack`
	* payload ([see below](#lgconfigjob_uuidadapter)):
		```javascript
		{
			"ADAPTER1": config,
			"ADAPTER2": config
		}
		```

#### /lg/config/{*job_uuid*}/{*adapter*}
* __GET__ - Return _job\_uuid_'s config/status per query for _adapter_
        * Request headers:
                * Accept: `application/json`, `application/x-msgpack`
* __POST__ - Update _adapter_'s config
        * Request headers:
                * Content-Type: `application/json`, `application/x-msgpack`
	* payload - two styles:
		* set/update primary query config:
			* __query__: if present, sets as primary flow, any missing fields are inherited from previous primary, and previous primary's autotasking is disabled
			* __filter__: query filter to append when generating new tasks
			* __enabled__: enable/disable this query entirely
			* __autotask__: enable/disable autotasking for this query (use of _pos_ as bookmark against logID to generate tasks)
			* __pos__: current logID bookmark for this query for this job
				```javascript
				{
					"query": string,
					"filter": string,
					"enabled": boolean,
					"autotask": boolean,
					"pos": uint
				}
				```
		* update zero or more secondary queries (see above, except _query_ must be present for each, and primary query is left as is):
			```javascript
			[
				config,
			]
			```

#### /lg/adapter/{*adapter*}
* __GET__/__POST__ - Return next task for _adapter_ based on job priority, query parameters, and posted body
        * Request headers:
                * Accept: `application/json`, `application/x-msgpack`
                * Content-Type: `application/json`, `application/x-msgpack`
	* parameters/payload - all fields are optional:
		* __query__ - limit tasks to be for a specific _query_ or queries (else round-robins through available)
		* __limit__ - limit task size to _limit_ records (default: __200__, does not apply to re-issued tasks)
		* __min\_age__ - skip tasks if touched less than _min\_age_ seconds ago (default: __60__)
		* __blacklist__ - skip provided list of tasks
			```javascript
			{
				"query": string,
				"limit": uint,
				"min_age": uint,
				"blacklist": list
			}
			```

#### /lg/adapter/{*adapter*}/{*job_uuid*}
* __POST__ - Manually exercise _adapter_ against _job\_uuid_, optionally using a query filter
        * Request headers:
                * Accept: `application/json`, `application/x-msgpack`
                * Content-Type: `application/json`, `application/x-msgpack`
	* returns number of chains injected into task queue
	* parameters/payload:
		* __query__ - optionally supply a specific _query_ (defaults to _adapter_'s primary query)
		* __filter__ - optionally supply additional query _filter_ to restrict (default: __None__)
			```javascript
			{
				"query": string,
				"filter": string
			}
			```

#### /lg/adapter/{*adapter*}/{*job_uuid*}/{*task_uuid*}
* __GET__ - Update task timestamp, return specific task
        * Request headers:
                * Accept: `application/json`, `application/x-msgpack`
* __HEAD__ - Update task timestamp
* __DELETE__ - Delete task
* __POST__ - Merge task results, then delete task (default) or update task timestamp
        * Request headers:
                * Content-Type: `application/json`, `application/x-msgpack`
	* payload:
		* __consume__: if true, delete task successful ingest, else just update task timestamp (default: __true__)
		* __nodes__: list of node objects
		* __edges__: list of edge objects
		* __chains__: list of node[/edge/node]* chains
		* __meta__: job graph metadata
		* __adapters__: job's adapters - see [`/lg/config/{*job_uuid*}`](#lgconfigjob_uuid) endpoint above
			```javascript
			{
				"consume": boolean,
				"nodes": list,
				"edges": list,
				"chains": list,
				"meta": dict,
				"adapters": dict
			}
			```
