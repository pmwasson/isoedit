import pygame
import pygame_gui

pygame.init()

pygame.display.set_caption('Quick Start')
window_surface = pygame.display.set_mode((800, 600))

background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

manager = pygame_gui.UIManager((800, 600))

menu_options = ['New','Load','Save','Quit']

menu = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(options_list=menu_options,
                                                            starting_option='File',
                                                            relative_rect=pygame.Rect((10,10),(80,22)),
                                                            manager=manager)

load_dialog = pygame_gui.windows.ui_file_dialog.UIFileDialog(rect=pygame.Rect((10,10),(700,500)), 
                                                             manager=manager,
                                                             window_title='File to load',
                                                             visible=False)

save_dialog = pygame_gui.windows.ui_file_dialog.UIFileDialog(rect=pygame.Rect((10,10),(700,500)), 
                                                             manager=manager,
                                                             window_title='File to save',
                                                             visible=False)

#hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((350, 275), (100, 50)),
#                                            text='Say Hello',
#                                            manager=manager)

clock = pygame.time.Clock()
is_running = True

while is_running:
    time_delta = clock.tick(60)/1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                if event.ui_element == load_dialog:
                    print("Load file:", event.text)
                if event.ui_element == save_dialog:
                    print("Save file:", event.text)

            if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if (event.text == 'New'):
                    print("New")
                elif (event.text == 'Load'):
                    load_dialog.enable()
                    load_dialog.show()
                elif (event.text == 'Save'):
                    save_dialog.enable()
                    save_dialog.show()
                elif (event.text == 'Quit'):
                    is_running = False



        manager.process_events(event)

    manager.update(time_delta)

    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)

    pygame.display.update()
