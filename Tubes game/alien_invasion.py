import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien
from pygame import mixer

class AlienInvasion:
    
    def __init__(self):
        """inisialisasi game dan membuat resources game"""
        pygame.init()
        self.settings = Settings()

        """#membuat layar game menjadi fullscreen
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height"""

        #membuat ukuran layar yang spesifik/ seusai yang diinginkan
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        self.bg_image = pygame.transform.smoothscale(self.settings.bg_image, self.screen.get_size())
        pygame.display.set_caption("Alien Invasion")

        #membuat perintah untuk menyimpan statistik game
        #membuat scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        #menambahkan musik ketika game dijalankan
        mixer.music.load("background.wav")
        mixer.music.play(-1)


        self._create_fleet()

        #membuat play button
        self.play_button = Button(self, "Start")


    def run_game(self):
        """memulai perulangan untuk game"""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self.bullets.update()
                self._update_bullets()
                self._update_aliens()
            
            self._update_screen()
    
    def _check_events(self):
        """menanggapi tombol yang ditekan dan pergerakan mouse"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button:
                    self._check_mousedown_events(event)
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """memulai game ketika pemain menakan tombol play"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:

            #mereset game statistik
            self.settings.initialize_dynamic_settings()
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            #menghapus semua sisa alien dan tembakan
            self.aliens.empty()
            self.bullets.empty()

            #membuat fleet baru dan membuat ship berada di tengah
            self._create_fleet()
            self.ship.center_ship()

            #menyembunyikan mouse 
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self,event):
        """menanggapi tombol yang ditekan"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
            #menambahkan musik ketika peluru dikeluarkan
            bullet_sound = mixer.Sound("laser.wav")
            bullet_sound.play()

    def _check_mousedown_events(self, event):
        """membuat mouse dapat melakukan tembakan"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 or event.button == 5:
                self._fire_bullet()

    def _check_keyup_events(self,event):
        """menanggapi tombol yang dilepas"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False;
    
    def _fire_bullet(self):
        """membuat peluru baru dan memasukan ke bullet group"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """ 
            - memperbaharui posisi peluru dan menghapus peluru lama
            - memperbaharui posisi peluru
        """

        self.bullets.update()

        #menghapus peluru lama
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                 self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()
    
    def _check_bullet_alien_collisions(self):
        """
            - menanggapi tabrakan peluru-alien
            - menghapus semua peluru dan alien yang telah bertabrakan
        """
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
        
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()
            #menambahkan musik ketika alien dan peluru bertabrakan
            explosion_sound = mixer.Sound("explosion.wav") 
            explosion_sound.play()

        if not self.aliens:
            #menghancurkan peluru yang ada dan membuat armada kapal baru
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            #mengatur penambahan level
            self.stats.level += 1
            self.sb.prep_level()
    

    def _update_aliens(self):
        """
            - mengecek jika armada kapal telah di tepi
            - mengupdate posisi alien di armada kapal
        """
        self._check_fleet_edges()
        self.aliens.update()

        #untuk melihat pakah alien dan kapal telah bertabrakan
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
        #print("Ship hit!!")

        #melihat alien menabrak batas bawah layar
        self._check_aliens_bottom()
        
    def _ship_hit(self):
        """Menanggapi kapal yang telah ditabrak alien"""

        if self.stats.ships_left > 0:
            #mengaurai kapal kiri dan update scoreboard
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            #menghapus semua sisa alien dan peluru
            self.aliens.empty()
            self.bullets.empty()

            #membuat armada kapal baru dan membuatnya di tengah
            self._create_fleet()
            self.ship.center_ship()

            #Pause.
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _create_fleet(self):
        """membuat fleet alien"""

        #membuat alien dan mencari nomor alien di baris
        #membuat satu alien berjarak dengan yang lainnya
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2*alien_width)
        number_aliens_x = available_space_x // (2*alien_width)

        #menentukan nomor baris dari alien sesuai layar
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (3*alien_height) - ship_height)
        number_rows = available_space_y // (2*alien_height)

        #membuat alien memenuhi fleet
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)
    
    def _create_alien(self, alien_number, row_number):
        #membuat alien dan meletakannya di baris
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2*alien_width*alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)
    
    def _check_fleet_edges(self):
        """menanggapi dengan tepat jika alien mencapai tepi"""
        for alien in self.aliens.sprites():
            if  alien.check_edges():
                self._change_fleet_direction()
                break
    
    def _change_fleet_direction(self):
        """meletakan seluruh fleet dan mengubah arah fleet"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        """update gambar di screen dan mengembalikan ke layar baru"""
        self.screen.fill(self.settings.bg_color)
        self.screen.blit(self.settings.bg_image, (0, 0))
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        #informasi score
        self.sb.show_score()

        #button jika game belum aktif
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()
    
    def _check_aliens_bottom(self):
        """mengecek apakah alien telah mencapai batas bawah layar"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                #Treat this the same as if the ship got hit.
                self._ship_hit()
                break

if __name__ == '__main__':
    #membuat instance game dan menjalankan game
    ai = AlienInvasion()
    ai.run_game()