angular.module('schdl.schedule', ['ngStorage', 'ngResource'])

.factory('Schedule', ['$localStorage', '$resource', 'School', 'User', function($localStorage, $resource, School, User) {
  var remote = $resource('/api/schedules/:school/:term/:section', {}, {
    update: {method: 'PUT'}
  });
  var recommender = $resource('/api/recommender/:school/:term');
  function get(termId) {
    if ($localStorage.user && $localStorage.user.schedules) {
      for (var i=0; i < $localStorage.user.schedules.length; i++) {
        var schedule = $localStorage.user.schedules[i];
        if (schedule.term.fragment == termId) {
          return schedule;
        }
      }
    }
  }
  function getShared(termId, secret) {
    return School.$promise.then(function() {
      return User.get({school: School.fragment, secret: secret}).$promise.then(function (user) {
        var schedule = user.schedules[0];
        schedule.user = user;
        return schedule;
      });
    });
  }
  function getRecommendations(schedule) {
    var courses = [];
    var exclude = [];
    if ($localStorage.user && $localStorage.user.schedules) {
      for (var i=0; i < $localStorage.user.schedules.length; i++) {
        var course_sections = $localStorage.user.schedules[i].course_sections;
        for (var j=0; j < course_sections.length; j++) {
          var section = course_sections[j];
          if (section.user_status == 'no') {
            exclude.push(section.course_continuity_id);
          } else {
            courses.push(section.course_continuity_id);
          }
        }
      }
    }
    return School.$promise.then(function() {
      if (School.enable_recommendations) {
        return recommender.query({school: School.fragment, term: schedule.term.fragment, course: courses, exclude: exclude});
      } else {
        return [];
      }
    });
  }
  function getCourseSection(term, course_section) {
    var schedule = get(term);
    if (angular.isDefined(schedule)) {
      for (var i=0; i < schedule.course_sections.length; i++) {
        var section = schedule.course_sections[i];
        if (section.fragment == course_section) {
          return {schedule: schedule, index: i, section: section};
        }
      }
    }
  }
  function getCourseSectionStatus(term, course_section) {
    var found = getCourseSection(term, course_section);
    if (angular.isDefined(found)) {
      return found.section.user_status;
    } else {
      return 'delete';
    }
  }
  function updateCourseSection(school, term, course_section, status) {
    function updateLocal(response) {
      if (response) {
        $localStorage.user = response;
      }
    }
    if (status == 'delete') {
      remote['delete']({school: school, term: term, section: course_section}, updateLocal);
    } else {
      remote.update({school: school, term: term, section: course_section}, {status: status}, updateLocal);
    }
  }
  return {
    Remote: remote,
    Get: get,
    GetShared: getShared,
    GetRecommendations: getRecommendations,
    GetCourseSectionStatus: getCourseSectionStatus,
    UpdateCourseSection: updateCourseSection
  };
}])

.factory('schdlStatuses', function() {
  var statuses = [
    { id: 'delete', text: 'Remove', tooltip: 'Remove this section from your schedule.', icon: 'trash', buttonText: 'Add to Schedule', buttonIcon: 'none' },
    { id: 'maybe', text: 'Interested', tooltip: 'You are considering enrolling in this course.', icon: 'star', presentOnly: true },
    { id: 'definitely', text: 'Decided to Take', tooltip: 'You definitely want to enroll in this course when the time comes.', icon: 'thumbs-up', presentOnly: true },
    { id: 'official', text: 'Officially Enrolled', tooltip: 'You have successfully enrolled in this course using your school\'s registration system.', icon: 'ok' },
    { id: 'no', text: 'Ruled Out', tooltip: 'You considered this section, but decided not to enroll in it.', icon: 'minus-sign', presentOnly: true }
  ];
  for (var i=0; i < statuses.length; i++) {
    var status = statuses[i];
    statuses[status.id] = status;
  }
  statuses.getText = function getText(id, button) {
    var status = statuses[id];
    if (button && status.buttonText) {
      return status.buttonText;
    } else {
      return status.text;
    }
  };
  return statuses;
})

.directive('schdlUserStatus', function() {
  return {
    restrict: 'E',
    scope: {
      signedIn: '=',
      register: '=',
      term: '=',
      termEnd: '=',
      section: '=',
      registrationId: '=',
      status: '='
    },
    controller: ['$scope', 'schdlStatuses', 'School', 'Schedule', function($scope, schdlStatuses, School, Schedule) {
      function getStatus() {
        $scope.userStatus = Schedule.GetCourseSectionStatus($scope.term, $scope.section);
      }
      $scope.isRestricted = function isRestricted(status) {
        return status == 'restricted' || status == 'closed_restricted';
      };
      $scope.statuses = schdlStatuses;
      $scope.update = function(newStatus) {
        Schedule.UpdateCourseSection(School.fragment, $scope.term, $scope.section, newStatus);
      };
      $scope.$on('schdlUserDataChanged', getStatus);
      $scope.termIsOver = function termIsOver() {
        var curDate = (new Date()).toISOString().substr(0,10);
        return curDate > $scope.termEnd;
      };
      getStatus();
    }],
    templateUrl: '/static/schedule/userStatus.tpl.html'
  };
})

.controller('ScheduleCtrl', ['$scope', '$routeParams', 'Schedule', 'titleService', 'schedule', '$q', 'schdlStatuses', '$modal', function($scope, $routeParams, Schedule, titleService, schedule, $q, schdlStatuses, $modal) {
  function getSchedule() {
    $q.when(Schedule.Get($routeParams.termId)).then(function(schedule) {
      setTitle(schedule);
      $scope.schedule = schedule;
      Schedule.GetRecommendations(schedule).then(function(r) {
          $scope.recommendations = r;
      });
    });
  }
  function setTitle(schedule) {
    titleService(schedule.term.name + ' Schedule');
  }
  $scope.isRuledOut = function(section) {
    return section.user_status == 'no';
  };
  $scope.notRuledOut = function(section) {
    return section.user_status != 'no';
  };
  $scope.showExportModal = function() {
    $modal.open({
      templateUrl: '/static/schedule/export.tpl.html',
      controller: 'ExportCtrl'
    });
  };
  $scope.schedule = schedule;
  $scope.statuses = schdlStatuses;
  Schedule.GetRecommendations(schedule).then(function(r) {
      $scope.recommendations = r;
  });
  setTitle(schedule);
  $scope.$on('schdlUserDataChanged', getSchedule);
}])

.controller('SharedScheduleCtrl', ['$scope', 'schedule', 'schdlStatuses', 'titleService', function($scope, schedule, schdlStatuses, titleService) {
  titleService(schedule.user.name + "'s " + schedule.term.name + ' Schedule');
  $scope.isRuledOut = function(section) {
    return section.user_status == 'no';
  };
  $scope.notRuledOut = function(section) {
    return section.user_status != 'no';
  };
  $scope.schedule = schedule;
  $scope.statuses = schdlStatuses;
}])

.controller('ExportCtrl', ['$scope', '$window', 'Routes', 'School', '$localStorage', '$modalInstance', function($scope, $window, Routes, School, $localStorage, $modalInstance) {
  $scope.icsUrl = $window.location.protocol + '//' + $window.location.host + Routes.iCal(School.fragment, $localStorage.user.secret);
  $scope.icsUrlHttp = 'http://' + $window.location.host + Routes.iCal(School.fragment, $localStorage.user.secret);
  $scope.close = function() {
    $modalInstance.close();
  };
}])

;
