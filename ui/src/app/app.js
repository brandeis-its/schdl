angular.module('schdl', [
  'angularytics',
  'ngRoute',
  'ngResource',
  'ngAnimate',
  'ngStorage',
  'ngTouch',
  'ngAria',
  'schdl.blockSchedule',
  'schdl.login',
  'schdl.register',
  'schdl.resetPasswd',
  'schdl.school',
  'schdl.term',
  'schdl.safeInput',
  'schdl.subject',
  'schdl.settings',
  'schdl.stopEvent',
  'schdl.student_interest',
  'schdl.course',
  'schdl.instructor',
  'schdl.schedule',
  'schdl.search',
  'schdl.verify',
  'templates-app',
  'templates-common',
  'ui.bootstrap'
])

.config(['$routeProvider', '$locationProvider', 'AngularyticsProvider', function($routeProvider, $locationProvider, AngularyticsProvider) {
  $locationProvider.html5Mode(true);
  $routeProvider.
    when('/', {
      resolve: {
        school: ['School', function(School) {
          return School.$promise;
        }]
      },
      controller: 'SchoolCtrl',
      templateUrl: '/static/school/school.tpl.html'
    }).
    when('/term/:termId', {
      controller: 'TermCtrl',
      templateUrl: '/static/term/term.tpl.html',
      resolve: {
        term: ['Term', '$route', 'School', function(Term, $route, School) {
          return School.$promise.then(function() {
            return Term.get({
              id: $route.current.params.termId,
              school: School.fragment
            }).$promise;
          });
        }]
      }
    }).
    when('/subject/:termId/:subjectId', {
      controller: 'SubjectCtrl',
      templateUrl: '/static/subject/subject.tpl.html',
      resolve: {
        subject: ['Subject', '$route', 'School', function(Subject, $route, School) {
          return School.$promise.then(function() {
            return Subject.get({
              id: $route.current.params.subjectId,
              school: School.fragment,
              term: $route.current.params.termId
            }, function(subject) {
              for (var i=0; i < subject.segments.length; i++) {
                var segment = subject.segments[i];
                for (var j=0; j < segment.courses.length; j++) {
                  var course = segment.courses[j];
                  course.requirements = School.getRequirements(course.requirements);
                }
              }
            }).$promise;
          });
        }]
      }
    }).
    when('/course/:termId/:courseId', {
      controller: 'CourseCtrl',
      templateUrl: '/static/course/course.tpl.html',
      resolve: {
        course: ['Course', '$route', 'School', function(Course, $route, School) {
          return School.$promise.then(function() {
            return Course.get({
              id: $route.current.params.courseId,
              school: School.fragment,
              term: $route.current.params.termId
            }, function(course) {
              course.requirements = School.getRequirements(course.requirements);
            }).$promise;
          });
        }]
      }
    }).
    when('/instructor/:instructorId', {
      controller: 'InstructorCtrl',
      templateUrl: '/static/instructor/instructor.tpl.html',
      resolve: {
        instructor: ['Instructor', '$route', 'School', function(Instructor, $route, School) {
          return School.$promise.then(function() {
            return Instructor.get({
              id: $route.current.params.instructorId,
              school: School.fragment
            }).$promise;
          });
        }]
      }
    }).
    when('/schedule/:termId', {
      controller: 'ScheduleCtrl',
      resolve: {
        schedule: ['$route', 'Schedule', '$q', function($route, Schedule, $q) {
          var schedule = Schedule.Get($route.current.params.termId);
          if (schedule) {
            return schedule;
          } else {
            // Trigger $routeChangeError
            return $q.reject({status: 404});
          }
        }]
      },
      templateUrl: '/static/schedule/schedule.tpl.html',
      requiresUser: true
    }).
    when('/schedule/:termId/:secret', {
      controller: 'SharedScheduleCtrl',
      resolve: {
        schedule: ['$route', 'Schedule', '$q', function($route, Schedule, $q) {
          return Schedule.GetShared($route.current.params.termId, $route.current.params.secret);
        }]
      },
      templateUrl: '/static/schedule/schedule.tpl.html'
    }).
    when('/search', {
      controller: 'SearchCtrl',
      resolve: {
        instructors: ['School', '$location', 'Search', function(School, $location, Search) {
          return School.$promise.then(function() {
            var instr = $location.search().instr;
            if (angular.isDefined(instr) && instr.length) {
              if (typeof instr == 'string' || instr instanceof String) {
                instr = [instr];
              }
              return Search.GetInstructors.query({
                school: School.fragment,
                instr: instr
              }).$promise;
              // TODO(eitan): do error handling here to return [] instead of failing altogether
            } else {
              return [];
            }
          });
        }],
        subjects: ['School', '$location', 'Search', function(School, $location, Search) {
          return School.$promise.then(function() {
            var params = $location.search();
            var subj = params.subj;
            if (angular.isDefined(subj) && subj.length) {
              if (typeof subj == 'string' || subj instanceof String) {
                subj = [subj];
              }
              return Search.GetSubjects.query({
                term: params.term,
                school: School.fragment,
                subj: subj
              }).$promise;
              // TODO(eitan): do error handling here to return [] instead of failing altogether
            } else {
              return [];
            }
          });
        }]
      },
      templateUrl: '/static/search/search.tpl.html'
    }).
    when('/verify', {
      controller: 'VerifyCtrl',
      resolve: {
        results: ['School', 'Verify', '$location', function(School, Verify, $location) {
          return School.$promise.then(function() {
            var params = $location.search();
            if (!angular.isDefined(params.secret)) {
              $location.path('/');
              return;
            }
            return Verify.save({
              school: School.fragment
            }, {
              secret: params.secret
            }).$promise;
          });
        }]
      },
      templateUrl: '/static/verify/verify.tpl.html'
    }).
    when('/privacy', {
      templateUrl: '/static/privacy/privacy.tpl.html'
    }).
    when('/terms', {
      templateUrl: '/static/terms/terms.tpl.html'
    }).
    when('/settings', {
      controller: 'SettingsCtrl',
      resolve: {
        school: ['School', function(School) {
          return School.$promise;
        }],
        user: ['$localStorage', '$q', function($localStorage, $q) {
          if ($localStorage.user) {
            return $localStorage.user;
          } else {
            return $q.reject({status: 403});
          }
        }]
      },
      templateUrl: '/static/settings/settings.tpl.html',
      requiresUser: true
    }).
    when('/registrar/student_interest', {
      controller: 'StudentInterestCtrl',
      resolve: {
        school: ['School', function(School) {
          return School.$promise;
        }]
      },
      templateUrl: '/static/student_interest/student_interest.tpl.html',
      requiresUser: true
    }).
    otherwise({
      resolve: {
        broken: ['$q', function($q) {
          // Trigger $routeChangeError
          return $q.reject({status: 404});
        }]
      }
    });
  AngularyticsProvider.setEventHandlers(['Google']);
}])

.controller('MainCtrl',
    ['$scope', '$rootScope', '$localStorage', 'Routes', 'Session', 'User', 'Schedule', '$modal', '$window', 'School', 'QuickSearch', '$location', 'titleService', '$route', '$http',
    function($scope, $rootScope, $localStorage, Routes, Session, User, Schedule, $modal, $window, School, QuickSearch, $location, titleService, $route, $http) {
  var school = $rootScope.school;
  school.$promise.then(function() {
    var today = new Date();
    today.setUTCHours(0);
    today.setUTCMinutes(0);
    today.setUTCSeconds(0);
    today.setUTCMilliseconds(0);
    today = today.toJSON();
    school.future = [];
    school.past = [];
    school.current = [];
    for (var i=0; i< school.terms.length; i++) {
      var term = school.terms[i];
      if (term.start > today) {
        school.future.push(term);
      } else if (term.end < today) {
        school.past.push(term);
      } else {
        school.current.push(term);
      }
    }
    if (school.current.length > 0) {
      school.defaultTerm = school.current[0].fragment;
    } else if (school.future.length > 0) {
      school.defaultTerm = school.future[0].fragment;
    } else if (school.past.length > 0) {
      school.defaultTerm = school.past[0].fragment;
    }
    $scope.quicksearch.term = school.defaultTerm;
  });
  $rootScope.Routes = Routes;
  $rootScope.$on('schdlUserDataChanged', function(event, oldValue, newValue) {
    // If logged in status has changed and current route requires user data, reload
    if (angular.isDefined(oldValue) != angular.isDefined(newValue) && $route.current && $route.current.requiresUser) {
      $route.reload();
    }
  });
  $rootScope.get_user_data = function() {
    User.get(function(user) {
      $localStorage.user = user;
    }, function(rejection) {
      // TODO(eitan): retry (careful to rate-limit, though)
    });
  };
  $rootScope.login = function() {
    $modal.open({
      templateUrl: '/static/login/login.tpl.html',
      controller: 'LoginCtrl'
    });
  };
  $rootScope.register = function() {
    $modal.open({
      templateUrl: '/static/register/register.tpl.html',
      controller: 'RegisterCtrl'
    });
  };
  $rootScope.resetPasswd = function() {
    $modal.open({
      templateUrl: '/static/resetPasswd/resetPasswd.tpl.html',
      controller: 'ResetPasswdCtrl'
    });
  };
  $scope.logout = function() {
    Session['delete'](null, function() {
      $localStorage.user = null;
    });
  };
  $scope.navError = false;
  $scope.$on('$routeChangeError', function(event, current, prev, rejection) {
    $scope.navError = true;
    if (rejection.status == 404) {
        $scope.navError = 404;
        titleService('Not Found');
    } else if (rejection.status == 403) {
        $scope.navError = 403;
        titleService('Login Required');
        $scope.login();
        // TODO(eitan): trigger reload when login succeeds
    } else {
        $scope.navError = true;
        titleService('Error');
    }
  });
  $scope.$on('$routeChangeSuccess', function() {
    $scope.navError = false;
  });
  $scope.$window = $window;
  $rootScope.$storage = $localStorage;
  $rootScope.$watch(function() {
    return angular.toJson($localStorage.user);
  }, function (newValue, oldValue) {
    $rootScope.$broadcast('schdlUserDataChanged', oldValue, newValue);
  });
  $rootScope.$watch(function() {
    return $http.pendingRequests.length;
  }, function (newValue) {
    $rootScope.pendingRequests = newValue;
  });
  $rootScope.get_user_data();
  $scope.quicksearch = function(term, query) {
    return QuickSearch.query({id: term, school: school.fragment, query: query}).$promise;
  };
  $scope.quicksearch.jump = function(term, obj) {
    $location.path(Routes.Course(school.fragment, term, obj.fragment));
    $scope.quicksearch.course = '';
  };
  $scope.search = function(term, query) {
    $location.path('/search');
    var search = {term: term};
    if (angular.isDefined(query) && query.length) {
      search.q = query;
    }
    $location.search(search);
  };
}])

.filter('columns', [function() {
  return function(items, cols, min) {
    var prop = '__columns_' + items.length + '_' + cols + '_' + min + '__';
    if (!items.hasOwnProperty(prop)) {
      if (angular.isDefined(min) && items.length < min) {
        items[prop] = [items];
      } else {
        var out = [];
        var n = Math.ceil(items.length / cols);
        for (var i=0; i < cols; i++) {
          out.push(items.slice(i * n, i * n + n));
        }
        items[prop] = out;
      }
    }
    return items[prop];
  };
}])

.filter('schdlTime', [function() {
  return function(minutes) {
    var hours = Math.floor(minutes/60);
    minutes = minutes - 60 * hours;
    var sign = 'AM';
    if (hours === 0) {
      hours = 12;
    } else if (hours == 12) {
      sign = 'PM';
    } else if (hours > 12) {
      hours -= 12;
      sign = 'PM';
    }
    if (minutes < 10) {
      minutes = '0' + minutes;
    }
    return hours + ':' + minutes + ' ' + sign;
  };
}])

.filter('schdlDays', [function() {
  var day_names = {
    su: 'Su',
    m: 'M',
    tu: 'Tu',
    w: 'W',
    th: 'Th',
    f: 'F',
    sa: 'Sa'
  };
  var days = ['su', 'm', 'tu', 'w', 'th', 'f', 'sa'];
  return function(has_days) {
    var out = '';
    for (var i=0; i < days.length; i++) {
      var day = days[i];
      if (has_days.indexOf(day) != -1) {
        out += day_names[day];
      }
    }
    return out;
  };
}])


.factory('Routes', ['$rootScope', function ($rootScope) {
  function Schedule(school, term, secret) {
    var url = '/schedule' + '/' + term;
    if (secret) {
      url += '/' + secret;
    }
    return url;
  }
  function School(school) {
    return '/';
  }
  function Term(school, term) {
    if (term) {
      return '/term/' + term;
    }
  }
  function Subject(school, term, subject) {
    if (term && subject) {
      return '/subject/' + term + '/' + subject;
    }
  }
  function Course(school, term, course) {
    if (term && course) {
      return '/course/' + term + '/' + course;
    }
  }
  function Instructor(school, instructor) {
    return '/instructor/' + instructor;
  }
  function iCal(school, secret) {
    return '/api/ical/' + school + '/' + secret;
  }
  return {
    Schedule: Schedule,
    School: School,
    Term: Term,
    Subject: Subject,
    Course: Course,
    Instructor: Instructor,
    iCal: iCal
  };
}])

.factory('Session', ['$resource', function($resource) {
  return $resource('/api/session/:school');
}])

.factory('User', ['$resource', function($resource) {
  return $resource('/api/user/:school');
}])

.factory('titleService', ['$document', function($document) {
  return function(newTitle) {
    $document[0].title = newTitle;
  };
}])

.factory('QuickSearch', ['$resource', function($resource) {
  var QuickSearch = $resource('/api/quicksearch/:school/:id');
  return QuickSearch;
}])

.run(['Angularytics', function(Angularytics) {
  Angularytics.init();
}])

;
