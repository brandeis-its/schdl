angular.module('schdl.search', ['ngResource'])

.factory('Search', ['$resource', function($resource) {
  var Search = $resource('/api/search/:school');
  Search.Subjects = $resource('/api/subject_search/:school/:term');
  Search.GetSubjects = $resource('/api/subject_lookup/:school/:term');
  Search.Instructors = $resource('/api/instructor_search/:school');
  Search.GetInstructors = $resource('/api/instructor_lookup/:school');
  return Search;
}])

.controller('SearchCtrl', ['$scope', 'School', 'titleService', '$location', 'Search', 'subjects', 'instructors', function($scope, School, titleService, $location, Search, subjects, instructors) {
  var makeParams = function(termOnly) {
    var i;
    var params = {
      term: search.term,
      req: [],
      subj: [],
      instr: []
    };
    var isNull = true;
    if (search.q) {
      isNull = false;
      params.q = search.q;
    }
    if (search.independent_study) {
      params.independent_study = true;
    }
    if (search.closed) {
      params.closed = true;
    }
    for (var req in search.req) {
      if (search.req[req]) {
        isNull = false;
        params.req.push(req);
      }
    }
    if (search.reqMethod == 'any') {
      params.reqAny = true;
    }
    for (i=0; i < search.subjects.length; i++) {
        isNull = false;
        params.subj.push(search.subjects[i].id);
    }
    for (i=0; i < search.instructors.length; i++) {
        isNull = false;
        params.instr.push(search.instructors[i].id);
    }
    return (termOnly && isNull) ? null : params;
  };
  var search = function() {
    params = makeParams();
    $location.search(params);
  };
  search.q = '';
  search.req = {};
  search.reqMethod = 'all';
  search.subjects = subjects;
  search.instructors = instructors;

  // Translate URL params to search fields
  var params = $location.search();
  if (params.term) {
    search.term = params.term;
  } else {
    search.term = School.defaultTerm;
  }
  if (params.q) {
    search.q = params.q;
  }
  if (params.req) {
    if (typeof params.req == 'string' || params.req instanceof String) {
      search.req[params.req] = true;
    } else {
      for (var i = 0; i < params.req.length; i++) {
        search.req[params.req[i]] = true;
      }
    }
  }
  if (params.reqAny) {
    search.reqMethod = 'any';
  }
  if (angular.isDefined(params.closed)) {
    search.closed = true;
  }
  if (angular.isDefined(params.independent_study)) {
    search.independent_study = true;
  }
  // TODO(eitan): process params.subj and params.instr (maybe in resolver)

  // Do actual query from URL
  var query = makeParams(true);
  if (query !== null) {
    query.school = School.fragment;
    var results = Search.query(query, function() {
      for (var i=0; i < results.length; i++) {
        var course = results[i];
        course.requirements = School.getRequirements(course.requirements);
      }
      $scope.results = results;
    });
    results.term = query.term;
  }
  $scope.getsubjs = function(term, query) {
    return Search.Subjects.query({school: School.fragment, term: term, query: query}).$promise;
  };
  $scope.getinstrs = function(query) {
    return Search.Instructors.query({school: School.fragment, query: query}).$promise;
  };
  $scope.search = search;
  titleService('Search');
}])

;
